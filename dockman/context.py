# coding: utf-8

from __future__ import absolute_import

import os

import yaml

import dockman
from . import container as container_module
from .utils import NoConfigException, WrongConfigException


class Context(object):

    def __init__(self, path=None, config=None,
                 config_filename='dockman.yaml'):
        self.config_filename = config_filename

        if path is None:
            path = os.getcwd()

        if config is None:
            while True:
                filename = os.path.join(path, self.config_filename)

                if os.path.isfile(filename):
                    config = self.load_config(filename)
                    break

                head, tail = os.path.split(path)
                if not tail:
                    raise NoConfigException('No config file found')

                path = head

        self.project = os.path.split(path)[1]
        self.config = config
        self.path = path

        if not isinstance(config, dict):
            raise WrongConfigException('Config must be a dictionary.')

        # load the containers
        self.containers = {}
        self.containerlist = []

        containers = self.config.get('containers', {})
        if not isinstance(containers, dict):
            raise WrongConfigException('Containers must be a dictionary.')

        for name, config in containers.items():
            if not isinstance(config, dict):
                raise WrongConfigException('Container config must '
                                           'be a dictionary.')

            _container = container_module.Container(name,
                                                    self.project,
                                                    self.path,
                                                    config)
            self.containers.update({name: _container})
            self.containerlist.append(_container)

        # load the groups
        # groups maps the group name to the list of container instances
        self.groups = {}

        for name, containers in self.config.get('groups', {}).items():
            self.groups[name] = []
            for _container in containers:
                if _container not in self.containers:
                    message = 'Container %s in group %s not defined.'
                    raise WrongConfigException(message % (_container, name))
                self.groups[name].append(self.containers[_container])

        self.check_consistency()

    def load_config(self, path):
        with open(path, 'r') as f:
            config = yaml.load(f)

        return config

    def check_consistency(self):
        for c in self.containerlist:
            for dep in c.dependencies:
                if dep not in self.containers:
                    message = 'Container %s has an undefined dependency: %s'
                    raise WrongConfigException(message % (c.name, dep))

    def dependencies(self, container):
        """
        Returns a set of Container instances.
        """
        return set([self.containers[d] for d in container.dependencies])

    def reverse_dependencies(self, container):
        """
        Returns a set of Container instances.
        """
        ret = set()
        for c in self.containerlist:
            if container in self.dependencies(c):
                ret.add(c)
        return ret

    def _circular_msg(self, new, node, reverse):
        circular = node[node.index(new):] + [new]
        names = [c.name for c in circular]
        arrow = ' <- ' if reverse else ' -> '
        return 'Circular dependencies: ' + arrow.join(names)

    def _chain(self, seen=[], node=[], reverse=False):
        while node:
            # one unseen dependency needed
            current = node[-1]
            if reverse:
                deps = self.reverse_dependencies(current)
            else:
                deps = self.dependencies(current)
            unseen = [d for d in deps if d not in seen]
            if unseen:
                new = unseen[0]
                if new in node:
                    message = self._circular_msg(new, node, reverse)
                    raise WrongConfigException(message)

                node.append(new)
            else:
                seen.append(current)
                node.pop()

        return seen

    def chain(self, container):
        return self._chain(node=[container])

    def reverse_chain(self, container):
        return self._chain(node=[container], reverse=True)

    def run(self, interactive, container_name, extra):
        container = self.containers[container_name]
        for c in self.chain(container)[:-1]:
            c.start()
        if interactive:
            container.start_interactive(extra)
        else:
            container.start(extra)

    def up(self, group_name):
        group = self.groups[group_name]

        to_start = []
        for container in group:
            for dep in self.chain(container):
                if dep not in to_start:
                    to_start.append(dep)

        for c in to_start:
            c.start()

    def remove(self, container_name):
        container = self.containers[container_name]
        for c in self.reverse_chain(container):
            c.remove()

    def down(self, group_name):
        group = self.groups[group_name]

        to_stop = []
        for container in group:
            for dep in self.reverse_chain(container):
                if dep not in to_stop:
                    to_stop.append(dep)

        for c in to_stop:
            c.stop()

    def logs(self):
        containers = dockman.DOCKER.running_container_names(self.project)
        dockman.DOCKER.logs(containers)
