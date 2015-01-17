# coding: utf-8

from __future__ import absolute_import

import click

from . import command


@click.group()
def main():
    """Manage Docker containers with ease."""


@main.command()
def ps():
    """List existing containers."""
    command.ContextFreeCommand().ps()


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
    command.Command().run(interactive, container, extra)


@main.command()
@click.argument('group')
def up(group):
    command.Command().up(group)
    command.ContextFreeCommand().ps()


@main.command()
@click.argument('container')
def remove(container):
    """
    Stops and removes the given container and all child containers
    (those dependt on it).
    """
    command.Command().remove(container)
    command.ContextFreeCommand().ps()


@main.command()
@click.argument('group')
def down(group):
    command.Command().down(group)
    command.ContextFreeCommand().ps()
