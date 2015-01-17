# coding: utf-8

from __future__ import absolute_import

import os


class Container(object):

    def __init__(self, name, project, config, docker):
        self.name = name
        self.project = project
        self.config = config
        self.docker = docker
        self.project_name = '%s.%s' % (project, name)
        self.ports = config.get('ports', {})

        try:
            self.image = config['image']
        except KeyError:
            raise ('No image given for container %s' % self.name)

        # We can use ~ in the config file
        self.volumes = {}
        for hostvolume, containervolume in config.get('volumes', {}).items():
            _hostvolume = os.path.expanduser(hostvolume)
            self.volumes[_hostvolume] = containervolume

        self.env = {}
        for key, value in config.get('env', {}).items():
            if value is None:
                self.env[key] = os.environ.get(key, '')
            else:
                self.env[key] = value

        self.volumes_from = config.get('volumes_from', [])
        _vf = ['%s.%s' % (project, vf) for vf in self.volumes_from]
        self.project_volumes_from = _vf

        self.links = config.get('links', {})
        linkitems = self.links.items()
        _l = dict([('%s.%s' % (self.project, k), v) for k, v in linkitems])
        self.project_links = _l

    @property
    def dependencies(self):
        """
        Returns all dependencies of the container
        as a set of names as defined in the config.
        """
        deps = set(self.volumes_from)
        deps = deps.union(set(self.links.keys()))
        return deps

    @property
    def next_postfix(self):
        """
        Returns the next available integer for interactive container
        name postfix or None if the main container does not exist.
        """
        if self.state is None:
            return None

        for counter in xrange(1, 10000):
            name = '%s.%s' % (self.project_name, counter)
            if self.docker.getstate(name) is None:
                return counter

    @property
    def state(self):
        return self.docker.getstate(self.project_name)

    def start(self, extra=[]):
        yield (('e_', '%s ' % self.project_name))

        state = self.state
        if state:
            yield(('e_', 'already running ... '))
            yield(('g', '✔'))
        else:
            yield(('e_', 'starting ... '))
            try:
                if state is None:
                    extended_env = self.env
                    extended_env.update({'container_name': self.project_name})
                    volumes_from = self.project_volumes_from
                    self.docker.run(self.image, daemon=True,
                                    interactive=False, remove=False,
                                    name=self.project_name,
                                    volumes_from=volumes_from,
                                    volumes=self.volumes,
                                    ports=self.ports,
                                    links=self.project_links,
                                    env=extended_env, cmd=extra)
                else:
                    self.docker.start(self.project_name)
            except Exception as e:
                yield(('r', '✘'))
                yield(('r', str(e)))
                raise
            else:
                yield(('g', '✔'))

    def start_interactive(self, extra=[]):
        postfix = self.next_postfix

        if postfix:
            ports = {}
            name = '%s.%s' % (self.project_name, postfix)
        else:
            ports = self.ports
            name = self.project_name

        extended_env = self.env
        extended_env.update({'container_name': name})
        volumes_from = self.project_volumes_from
        self.docker.run(self.image, daemon=False,
                        interactive=True, remove=True,
                        name=name, volumes_from=volumes_from,
                        volumes=self.volumes, ports=ports,
                        links=self.project_links,
                        env=extended_env, cmd=extra)

    def stop(self):
        state = self.state

        yield (('e_', '%s ' % self.project_name))

        if state:
            yield (('e_', 'stopping ... '))
            try:
                self.docker.stop(self.project_name)
            except Exception as e:
                yield(('r', '✘'))
                yield(('r', str(e)))
                raise
        elif state is False:
            yield (('e_', 'already stopped ... '))
        else:
            yield (('e_', 'does not exist ... '))

        yield(('g', '✔'))

    def remove(self):
        state = self.state

        if state:
            for y in self.stop():
                yield y
            state = False

        yield (('e_', '%s ' % self.project_name))

        if state is None:
            yield (('e_', 'does not exist ... '))
        else:
            yield (('e_', 'removing ... '))
            try:
                self.docker.remove(self.project_name)
            except Exception as e:
                yield(('r', '✘'))
                yield(('r', str(e)))
                raise

        yield(('g', '✔'))

    # @property
    # def reverse_dependecies(self):
    #     containers = self.context.containers.items()
    #     return [k for k, v in containers if self.config_name in v.dependencies]

    # def _dependency(self, reverse=False):
    #     if reverse:
    #         return self.reverse_dependecies
    #     return self.dependencies

    # def _chain(self, seen=[], reverse=False):
    #     node = [self.config_name]
    #     while node:
    #         # one unseen dependency needed
    #         current = self.context.containers.get(node[-1])
    #         deps = current._dependency(reverse)
    #         unseen = [d for d in deps if d not in seen]

    #         if unseen:
    #             new = unseen[0]

    #             if new in node:
    #                 message = utils.print_circular(new, node)
    #                 self.context.fail(message)

    #             node.append(new)

    #         else:
    #             seen.append(current.config_name)
    #             node.pop()

    #     return seen

    # @property
    # def chain(self):
    #     return self._chain(seen=[], reverse=False)

    # @property
    # def reverse_chain(self):
    #     return self._chain(seen=[], reverse=True)

    # def start(self, extra=[]):
    #     """
    #     Ensures the container is in start state, which means
    #     start it if stopped, create if does not exist.
    #     """
    #     for container_name in self.chain[:-1]:
    #         self.context.containers[container_name]._start()
    #     self._start(extra)

    # def interactive(self, extra=[]):
    #     for container_name in self.chain[:-1]:
    #         self.context.containers[container_name]._start()
    #     self._interactive(extra)

    # def stop(self):
    #     """
    #     Ensures the container is stopped.
    #     """
    #     for container_name in self.reverse_chain:
    #         self.context.containers[container_name]._stop()

    # def remove(self):
    #     """
    #     Ensures the container is removed.
    #     """
    #     for container_name in self.reverse_chain:
    #         container = self.context.containers[container_name]
    #         container._stop()
    #         container._remove()
