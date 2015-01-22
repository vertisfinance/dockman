# coding: utf-8

from __future__ import absolute_import

import functools
import sys

import click
from yaml import Loader, SafeLoader

import dockman


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


def needs_context(func):
    def wrapper(*args, **kwargs):
        if dockman.CONTEXT is None:
            red('No config file found')
            sys.exit(1)
        else:
            return func(*args, **kwargs)

    return functools.update_wrapper(wrapper, func)
