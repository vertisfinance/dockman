# coding: utf-8

from __future__ import absolute_import

import os
import click

import dockman
from . import docker
from . import context
from . import utils


if os.environ.get('DOCKMAN_SUDO'):
    dockman.DOCKER = docker.Docker(command=['sudo', 'docker'])
else:
    dockman.DOCKER = docker.Docker()


try:
    dockman.CONTEXT = context.Context()
except context.NoConfigException:
    dockman.CONTEXT = None
except context.WrongConfigException as e:
    utils.red(str(e))


@click.group()
def main():
    """Manage Docker containers with ease."""


@main.command()
def ps():
    """List existing containers."""
    project = None if dockman.CONTEXT is None else dockman.CONTEXT.project
    dockman.DOCKER.ps(project)


@main.command()
@click.option('-i', '--interactive', is_flag=True)
@click.argument('container')
@click.argument('extra', nargs=-1)
@utils.needs_context
def run(interactive, container, extra):
    """
    Run the given command in the given container.
    Dependent containers will be created and started if needed.
    If ineractive falg set, the container will be started in
    interactive mode: -it, --rm. If the given container exists, a new one
    will be created with the name container.x, where x is the lowest available
    integer.
    """
    if container not in dockman.CONTEXT.containers:
        utils.red('No container named %s' % container)
    else:
        dockman.CONTEXT.run(interactive, container, extra)


@main.command()
@click.argument('group')
@utils.needs_context
def up(group):
    if group not in dockman.CONTEXT.groups:
        utils.red('No group %s defined.' % group)
    else:
        try:
            dockman.CONTEXT.up(group)
        except docker.DockerError:
            pass
    dockman.DOCKER.ps(dockman.CONTEXT.project)


@main.command()
@click.argument('container')
@utils.needs_context
def remove(container):
    """
    Stops and removes the given container and all child containers
    (those dependt on it).
    """
    if container not in dockman.CONTEXT.containers:
        utils.red('No container named %s' % container)
    else:
        dockman.CONTEXT.remove(container)
    dockman.DOCKER.ps(dockman.CONTEXT.project)


@main.command()
@click.argument('group')
@utils.needs_context
def down(group):
    if group not in dockman.CONTEXT.groups:
        utils.red('No group %s defined.' % group)
    else:
        dockman.CONTEXT.down(group)
    dockman.DOCKER.ps(dockman.CONTEXT.project)


@main.command()
@click.argument('group')
@utils.needs_context
def logs(group):
    # if container not in dockman.CONTEXT.containers:
    #     utils.red('No container named %s' % container)
    # else:
    #     dockman.DOCKER.logs(container)
    try:
        dockman.CONTEXT.logs(group)
    except KeyboardInterrupt:
        dockman.DOCKER.stopthreads()
    utils.echo('')
