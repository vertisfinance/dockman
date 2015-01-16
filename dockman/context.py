# coding: utf-8

from __future__ import absolute_import

import os

from . import utils


class Container(object):

    def __init__(self, config_name, context):
        self.config_name = config_name
        self.context = context
        self.project = project = context.project

        try:
            params = context.config['containers'][config_name]
        except:
            context.fail('Could not load parameters for %s' % config_name)

        # We can use ~ in the config file
        volumes = {}
        for k, v in params.get('volumes', {}).items():
            host_dir = os.path.expanduser(k)
            volumes[host_dir] = v

        _env = params.get('env', {})
        env = {}
        for k, v in _env.items():
            if v is None:
                env[k] = os.environ.get(k, '')
            else:
                env[k] = v

        self.volumes_from = volumes_from = params.get('volumes_from', [])
        self._volumes_from = ['%s.%s' % (project, c) for c in volumes_from]

        self.links = links = params.get('links', {})
        self._links = {}
        for k, v in links.items():
            self._links['%s.%s' % (project, k)] = v

        self.image = params['image']
        self.name = '%s.%s' % (project, config_name)
        self.volumes = volumes
        self.ports = params.get('ports', {})
        self.env = env

    @property
    def state(self):
        return utils.getstate(self.name)

    @property
    def next_shell_postfix(self):
        """
        Returns the next available integer for interactive container
        name postfix or None if the main container does not exist.
        """
        if self.state is None:
            return None

        for counter in xrange(1, 10000):
            name = '%s.%s' % (self.name, counter)
            if utils.getstate(name) is None:
                return counter

    @property
    def dependencies(self):
        """Returns all dependencies of the container."""
        deps = set(self.volumes_from)
        deps = deps.union(set(self.links.keys()))
        return deps

    @property
    def reverse_dependecies(self):
        containers = self.context.containers.items()
        return [k for k, v in containers if self.config_name in v.dependencies]

    def _dependency(self, reverse=False):
        if reverse:
            return self.reverse_dependecies
        return self.dependencies

    def _chain(self, seen=[], reverse=False):
        node = [self.config_name]
        while node:
            # one unseen dependency needed
            current = self.context.containers.get(node[-1])
            deps = current._dependency(reverse)
            unseen = [d for d in deps if d not in seen]

            if unseen:
                new = unseen[0]

                if new in node:
                    message = utils.print_circular(new, node)
                    self.context.fail(message)

                node.append(new)

            else:
                seen.append(current.config_name)
                node.pop()

        return seen

    @property
    def chain(self):
        return self._chain(seen=[], reverse=False)

    @property
    def reverse_chain(self):
        return self._chain(seen=[], reverse=True)

    def _start(self, extra=[]):
        state = self.state

        if state:
            return

        extended_env = self.env
        extended_env.update({'container_name': self.name})
        run_params = utils.run_params(self.image,
                                      daemon=True,
                                      interactive=False,
                                      remove=False,
                                      name=self.name,
                                      volumes_from=self._volumes_from,
                                      volumes=self.volumes,
                                      ports=self.ports,
                                      links=self._links,
                                      env=extended_env,
                                      cmd=extra)

        utils.vecho_('starting %s ... ' % self.name, self.context.verbose)
        try:
            if state is None:
                utils.docker_run(run_params)
            else:
                utils.docker_start(self.name, verbose=False)
        except Exception as e:
            utils.vred('✘', self.context.verbose)
            utils.vred(str(e), self.context.verbose)
            raise
        else:
            utils.vgreen('✔', self.context.verbose)

    def start(self, extra=[]):
        """
        Ensures the container is in start state, which means
        start it if stopped, create if does not exist.
        """
        for container_name in self.chain[:-1]:
            self.context.containers[container_name]._start()
        self._start(extra)

    def _interactive(self, extra=[]):
        postfix = self.next_shell_postfix

        if postfix:
            ports = {}
            name = '%s.%s' % (self.name, postfix)
        else:
            ports = self.ports
            name = self.name

        extended_env = self.env
        extended_env.update({'container_name': name})
        run_params = utils.run_params(self.image,
                                      daemon=False,
                                      interactive=True,
                                      remove=True,
                                      name=name,
                                      volumes_from=self._volumes_from,
                                      volumes=self.volumes,
                                      ports=ports,
                                      links=self._links,
                                      env=extended_env,
                                      cmd=extra)

        utils.run_docker_intaractive(run_params)

    def interactive(self, extra=[]):
        for container_name in self.chain[:-1]:
            self.context.containers[container_name]._start()
        self._interactive(extra)

    def _stop(self):
        if self.state:
            utils.docker_stop(self.name, self.context.verbose)

    def stop(self):
        """
        Ensures the container is stopped.
        """
        for container_name in self.reverse_chain:
            self.context.containers[container_name]._stop()

    def _remove(self):
        if self.state is not None:
            utils.docker_remove(self.name, self.context.verbose)

    def remove(self):
        """
        Ensures the container is removed.
        """
        for container_name in self.reverse_chain:
            container = self.context.containers[container_name]
            container._stop()
            container._remove()


class Context(object):

    default_name = 'dockman.yaml'

    def __init__(self):
        self.loaded = False

    def load(self, verbose=True):
        self.verbose = verbose
        path = os.getcwd()

        while True:
            filename = os.path.join(path, self.default_name)

            if os.path.isfile(filename):
                break

            head, tail = os.path.split(path)
            if not tail:
                self.fail('Config file (%s) not found' % self.default_name)

            path = head

        self.project = os.path.split(path)[1]
        self.config = utils.load_config(filename) or {}

        containers = self.config.get('containers', {})
        containers = [Container(name, self) for name in containers]
        self.containers = dict([(c.config_name, c) for c in containers])

        self.check_consistency()

        self.groups = {}
        for k, v in self.config.get('groups', {}).items():
            self.groups[k] = []
            for container in v:
                if container not in self.containers:
                    message = 'Container %s in group %s not defined.'
                    self.fail(message % (container, k))
                self.groups[k].append(self.containers[container])

        self.loaded = True
        return self  # so we can write ctx = Context().load()

    def check_consistency(self):
        for name, container in self.containers.items():
            volumes_from = container.volumes_from
            links = container.links.keys()

            a = [c for c in volumes_from if c not in self.containers]
            if a:
                message = 'Undefined containers: %s/volumes_from: %s'
                clist = ' '.join(a)
                self.fail(message % (name, clist))

            a = [c for c in links if c not in self.containers]
            if a:
                message = 'Undefined containers: %s/links: %s'
                clist = ' '.join(a)
                self.fail(message % (name, clist))

    def fail(self, message):
        if self.verbose:
            utils.red(message)
        raise Exception(message)
