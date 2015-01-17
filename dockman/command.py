# coding: utf-8

from __future__ import absolute_import

import functools

import click
from yaml import Loader, SafeLoader

from . import context as context_module
from . import docker as docker_module


# --------------------
# Override the default yaml string handling function
# to always return unicode objects
def construct_yaml_str(self, node):
    return self.construct_scalar(node)
Loader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)
SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)
# --------------------


red = functools.partial(click.secho, fg='red')
red_ = functools.partial(click.secho, fg='red', nl=False)
green = functools.partial(click.secho, fg='green')
green_ = functools.partial(click.secho, fg='green', nl=False)
yellow = functools.partial(click.secho, fg='yellow')
yellow_ = functools.partial(click.secho, fg='yellow', nl=False)

echo = click.echo
echo_ = functools.partial(click.echo, nl=False)

colorfunc = {'r': red, 'r_': red_, 'g': green, 'g_': green_,
             'y': yellow, 'y_': yellow_, 'e': echo, 'e_': echo_}


class ContextFreeCommand(object):

    def __init__(self, context_class=context_module.Context,
                 docker=docker_module.Docker()):
        self.docker = docker
        try:
            self.context = context_class(docker=docker)
        except:
            self.context = None

    def ps(self):
        project = None if self.context is None else self.context.project
        for color, msg in self.docker.info_lines(project):
            colorfunc.get(color)(msg)


class Command(object):

    def __init__(self, context_class=context_module.Context,
                 docker=docker_module.Docker()):
        try:
            self.context = context_class(docker=docker)
        except Exception as e:
            red(str(e))

    def run(self, interactive, container, extra):
        if container not in self.context.containers:
            red('No container named %s' % container)
        else:
            for color, msg in self.context.run(interactive, container, extra):
                colorfunc.get(color)(msg)

    def up(self, group):
        if group not in self.context.groups:
            red('No group %s defined.' % group)
        else:
            for color, msg in self.context.up(group):
                colorfunc.get(color)(msg)

    # def remove(self, container):
    #     if container not in self.context.containers:
    #         red('No container named %s' % container)
    #     else:
    #         for color, msg in self.context.remove(container):
    #             colorfunc.get(color)(msg)

    def down(self, group):
        if group not in self.context.groups:
            red('No group %s defined.' % group)
        else:
            for color, msg in self.context.down(group):
                colorfunc.get(color)(msg)
