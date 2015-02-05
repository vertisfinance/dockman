# coding: utf-8

from __future__ import absolute_import

import os

import dockman
from . import utils
from . import docker


class Container(object):

    def __init__(self, name, project, config):
        self.name = name
        self.project = project
        self.config = config
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
        _cmd = config.get('cmd', None)
        self.cmd = [_cmd] if _cmd else []

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
            if dockman.DOCKER.getstate(name) is None:
                return counter

    @property
    def state(self):
        return dockman.DOCKER.getstate(self.project_name)

    def start(self, extra=[]):
        utils.echo_('%s ' % self.project_name)

        state = self.state
        if state:
            utils.echo_('already running ... ')
            utils.green('✔')
        else:
            utils.echo_('starting ... ')
            try:
                if state is None:
                    extended_env = self.env
                    extended_env.update({'container_name': self.project_name})
                    volumes_from = self.project_volumes_from
                    dockman.DOCKER.run(self.image, daemon=True,
                                       interactive=False, remove=False,
                                       name=self.project_name,
                                       volumes_from=volumes_from,
                                       volumes=self.volumes,
                                       ports=self.ports,
                                       links=self.project_links,
                                       env=extended_env,
                                       cmd=(extra or self.cmd))
                else:
                    dockman.DOCKER.start(self.project_name)
            except docker.DockerError as e:
                utils.red('✘')
                utils.red(str(e))
                raise e
            else:
                utils.green('✔')

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
        dockman.DOCKER.run(self.image, daemon=False,
                           interactive=True, remove=True,
                           name=name, volumes_from=volumes_from,
                           volumes=self.volumes, ports=ports,
                           links=self.project_links,
                           env=extended_env,
                           cmd=(extra or self.cmd))

    def stop(self):
        state = self.state

        utils.echo_('%s ' % self.project_name)

        if state:
            utils.echo_('stopping ... ')
            try:
                dockman.DOCKER.stop(self.project_name)
            except Exception as e:
                utils.red('✘')
                utils.red(str(e))
                raise e
        elif state is False:
            utils.echo_('already stopped ... ')
        else:
            utils.echo_('does not exist ... ')

        utils.green('✔')

    def remove(self):
        state = self.state

        if state:
            self.stop()
            state = False

        utils.echo_('%s ' % self.project_name)

        if state is None:
            utils.echo_('does not exist ... ')
        else:
            utils.echo_('removing ... ')
            try:
                dockman.DOCKER.remove(self.project_name)
            except Exception as e:
                utils.red('✘')
                utils.red(str(e))

                raise e

        utils.green('✔')
