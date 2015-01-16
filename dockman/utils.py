# coding: utf-8

from __future__ import absolute_import

import functools
import os
import subprocess
import json

import click
import yaml
from yaml import Loader, SafeLoader


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


def vfactory(func):
    def retfunc(str, verbose=False):
        if verbose:
            func(str)
    return retfunc


(vred, vred_,
 vgreen, vgreen_,
 vyellow, vyellow_,
 vecho, vecho_) = tuple(map(vfactory, (red, red_,
                                       green, green_,
                                       yellow, yellow_,
                                       echo, echo_)))


def run_docker_intaractive(params):
    subprocess.call(['docker', 'run'] + params)


def run_docker_command(params):
    try:
        output = subprocess.check_output(['docker'] + params,
                                         stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise Exception(e.output)
    else:
        return output


def load_config(path):
    with open(path, 'r') as f:
        config = yaml.load(f)
    return config


def get_container_ids():
    params = ['ps', '-a', '-q']
    output = run_docker_command(params)
    return output.splitlines()


def get_container_info():
    ids = get_container_ids()
    if ids:
        params = ['inspect'] + get_container_ids()
        output = run_docker_command(params)
        return json.loads(output)
    else:
        return []


def getstate(container_name):
    """Returns None if the container does not exits,
       False if not running, True if running."""
    params = ['inspect', '--format="{{.State.Running}}"', container_name]
    try:
        output = run_docker_command(params)
    except:
        return None
    else:
        output = output.strip()
        if output == 'true':
            return True
        elif output == 'false':
            return False


def print_containers(project=None):
    """Prints existing containers."""
    info = get_container_info()

    infolist = []
    for cinfo in info:
        name = cinfo['Name'][1:]

        if project:
            splitted = name.split('.')
            if len(splitted) == 1 or splitted[0] != project:
                continue

        if cinfo['State']['Running']:
            state = 'running'
        else:
            state = 'exited'

        bind_description_list = []
        ports = cinfo['NetworkSettings']['Ports']
        if not ports:
            ports = {}

        for container_port, bind_list in ports.items():
            if bind_list is None:
                bind_list = []
            container_port = container_port.split('/')[0]
            for bind_item in bind_list:
                desc = '%s -> %s:%s' % (container_port,
                                        bind_item['HostIp'],
                                        bind_item['HostPort'])
                bind_description_list.append(desc)
        if not bind_description_list:
            bind_description_list = ['']

        infolist.append((name, state, bind_description_list))

    if infolist:
        max_name_len = max([len(x[0]) + 2 for x in infolist])
        max_state_len = max([len(x[1]) + 2 for x in infolist])
        all_bind_desc = sum([x[2] for x in infolist], [])
        max_bind_len = max([len(x) for x in all_bind_desc])

        # compensate when no bind info
        if max_bind_len == 0:
            max_bind_len = -2

        max_len = max_name_len + max_state_len + max_bind_len
        yellow('-' * max_len)
        fmt = '{0:<%s}{1:<%s}{2}' % (max_name_len, max_state_len)

        for name, state, bind_description_list in infolist:
            message = fmt.format(name, state, bind_description_list[0])
            if state == 'running':
                green(message)
            else:
                echo(message)

            for other in bind_description_list[1:]:
                message = fmt.format('', '', other)
                if state == 'running':
                    green(message)
                else:
                    echo(message)
        yellow('-' * max_len)


def print_circular(new, node, verbose=False):
    circular = node[node.index(new):] + [new]
    return 'Circular dependencies: ' + ' -> '.join(circular)


def docker_start(name, verbose=True):
    vecho_('starting %s ... ' % name, verbose)
    try:
        output = run_docker_command(['start', name])
    except:
        vred('✘', verbose)
        raise
    else:
        vgreen('✔', verbose)

    return output


def docker_stop(name, verbose=True):
    vecho_('stopping %s ... ' % name, verbose)
    try:
        output = run_docker_command(['stop', name])
    except:
        vred('✘', verbose)
        raise
    else:
        vgreen('✔', verbose)

    return output


def docker_remove(name, verbose=True):
    vecho_('removing %s ... ' % name, verbose)
    try:
        output = run_docker_command(['rm', name])
    except:
        vred('✘', verbose)
        raise
    else:
        vgreen('✔', verbose)

    return output


def docker_run(params):
    return run_docker_command(['run'] + params)


# def ensure_running(container, config, verbose=False):
#     """
#     Make sure the container is running. Does not care about dependencies.
#     """
#     state = getstate(container)

#     if state is None:
#         start_with_config(container, config, verbose)
#     elif state is False:
#         start_container(container, verbose)
#     else:
#         if verbose:
#             echo_('Dependent container %s already running ... ' % container)
#             green('✔')


# def start_container(name, verbose=False):
#     """Starts an existing container."""

#     if verbose:
#         echo_('Starting %s ... ' % name)

#     params = ['docker', 'start', name]
#     try:
#         subprocess.check_output(params, stderr=subprocess.STDOUT)
#     except subprocess.CalledProcessError:
#         if verbose:
#             red('✘')
#         raise
#     else:
#         green('✔')


# def start_with_config(container, config, verbose=False):
#     if verbose:
#         echo_('Starting %s ... ' % container)

#     params = params_from_config(container, config)
#     params['verbose'] = verbose

#     try:
#         run_docker(**params)
#     except Exception:
#         if verbose:
#             red('✘')
#         raise
#     else:
#         if verbose:
#             green('✔')


# def params_from_config(container, config):
#     container_config = config['containers'][container]

#     env = container_config.get('env', {})
#     i = env.items()
#     env = dict([(k, os.environ.get(k, '') if v is None else v) for k, v in i])
#     env['container_name'] = container

#     volumes = {}
#     for k, v in container_config.get('volumes', {}).items():
#         host_dir = os.path.expanduser(k)
#         volumes[host_dir] = v

#     params = {'image': container_config['image'],
#               'daemon': True,
#               'interactive': False,
#               'remove': False,
#               'name': container,
#               'volumes_from': container_config.get('volumes_from', []),
#               'volumes': volumes,
#               'ports': container_config.get('ports', {}),
#               'links': container_config.get('links', {}),
#               'env': env,
#               'cmd': []}

#     return params


# def remove_container(name, verbose=False):
#     params = ['docker', 'rm', name]

#     if verbose:
#         echo_('Removing %s ... ' % name)

#     try:
#         subprocess.check_output(params, stderr=subprocess.STDOUT)
#     except subprocess.CalledProcessError as e:
#         message = 'Could not remove container %s:\n%s' % (name, e)
#         if verbose:
#             red('✘')
#         raise Exception(message)

#     if verbose:
#         green('✔')


# def stop_container(name, verbose=False):
#     state = getstate(name)
#     if state:
#         params = ['docker', 'stop', name]

#         if verbose:
#             echo_('Stopping %s ... ' % name)

#         subprocess.check_output(params, stderr=subprocess.STDOUT)

#         if verbose:
#             green('✔')
#     else:
#         if verbose:
#             echo_('Container %s is not running ... ' % name)
#             green('✔')


# def stop_and_remove(container, verbose=False):
#     state = getstate(container)
#     if state is None:
#         return

#     if state:
#         stop_container(container, verbose)

#     state = getstate(container)
#     if state is None:
#         return

#     remove_container(container, verbose)


def run_params(image,
               daemon=False,
               interactive=True,
               remove=True,
               name='',
               volumes_from=[],
               volumes={},
               ports={},
               links={},
               env={},
               cmd=[]):

    _args = []

    if daemon:
        remove = False
        _args.append('-d')

    if interactive:
        _args.append('-it')

    if remove:
        _args.append('--rm')

    if name:
        _args += ['--name', name]

    for v in volumes_from:
        _args += ['--volumes-from', v]

    for host_dir, container_dir in volumes.items():
        _args += ['-v', '%s:%s' % (host_dir, container_dir)]

    for host_port, container_port in ports.items():
        _args += ['-p', '%s:%s' % (host_port, container_port)]

    for link_name, alias in links.items():
        _args += ['--link', '%s:%s' % (link_name, alias)]

    for var_name, value in env.items():
        _args += ['-e', "%s=%s" % (var_name, value)]

    _args.append(image)
    _args += cmd

    return _args


# def run_docker(image,
#                daemon=False,
#                interactive=True,
#                remove=True,
#                name='',
#                volumes_from=[],
#                volumes={},
#                ports={},
#                links={},
#                env={},
#                cmd=[]):
#     """Runs the docker command with arguments derived from given parameters."""

#     _args = ['docker', 'run']
#     _args += run_params(image, daemon, interactive, remove,
#                         name, volumes_from, volumes, ports,
#                         links, env, cmd)

#     try:
#         subprocess.check_output(_args, stderr=subprocess.STDOUT)
#     except subprocess.CalledProcessError as e:
#         stop_and_remove(name)
#         raise Exception(e.output)
