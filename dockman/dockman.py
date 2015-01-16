# coding: utf-8

from __future__ import absolute_import

import sys

import click

from . import utils
from . import context


@click.group()
def main():
    """Manage Docker containers with ease."""


@main.command()
def ps():
    """List existing containers."""
    try:
        ctx = context.Context().load()
    except:
        utils.print_containers()
    else:
        utils.print_containers(ctx.project)


@main.command()
@click.option('-i', '--interactive', is_flag=True)
@click.argument('container')
@click.argument('extra', nargs=-1)
def run(interactive, container, extra):
    """
    Run the given command in the given container.
    Dependent containers will be created and started if needed.
    If ineractive falg set, the container will be started in
    interactive mode: -it, --rm. If the given container exists, a new one
    will be created with the name container.x, where x is the lowest available
    integer.
    """
    ctx = context.Context().load()

    try:
        container = ctx.containers[container]
    except KeyError:
        utils.red('Container %s not found in config.' % container)
        sys.exit(1)

    if interactive:
        container.interactive(extra)
    else:
        container.start(extra)


@main.command()
@click.argument('container')
def remove(container):
    """
    Stops and removes the given container and all child containers
    (those dependt on it).
    """
    ctx = context.Context().load()

    try:
        container = ctx.containers[container]
    except KeyError:
        utils.red('Container %s not found in config.' % container)
        sys.exit(1)

    container.remove()

    utils.print_containers(ctx.project)


@main.command()
@click.argument('group')
def up(group):
    ctx = context.Context().load()

    # is the container present in config?
    if group not in ctx.config['groups']:
        utils.red('Group %s not defined in the config file' % group)
        sys.exit(1)

    try:
        for container in ctx.groups[group]:
            container.start()
    except:
        pass
    finally:
        utils.print_containers(ctx.project)


@main.command()
@click.argument('group')
def down(group):
    ctx = context.Context().load()

    # is the container present in config?
    if group not in ctx.config['groups']:
        utils.red('Group %s not defined in the config file' % group)
        sys.exit(1)

    for container in ctx.groups[group]:
        container.stop()

    utils.print_containers(ctx.project)
