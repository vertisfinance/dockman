# coding: utf-8

from __future__ import absolute_import

import subprocess
import json


class Docker(object):
    def __init__(self, command=['docker']):
        self.command = command

    def execute(self, params):
        cmd = self.command + params

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise Exception(e.output)
        else:
            return output

    def execute_interactive(self, params):
        cmd = self.command + params
        subprocess.call(cmd)

    def run(self, image, daemon=True, interactive=False,
            remove=False, name='', volumes_from=[], volumes={},
            ports={}, links={}, env={}, cmd=[]):

        _args = ['run']

        if daemon:
            remove = False
            interactive = False
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

        if interactive:
            return self.execute_interactive(_args)
        else:
            return self.execute(_args)

    def start(self, container_name):
        self.execute(['start', container_name])

    def stop(self, container_name):
        self.execute(['stop', container_name])

    def remove(self, container_name):
        self.execute(['rm', container_name])

    def getstate(self, container_name):
        """
        Returns None if the container does not exits,
        False if not running, True if running.
        """
        params = ['inspect', '--format="{{.State.Running}}"', container_name]
        try:
            output = self.execute(params)
        except:
            return None
        else:
            output = output.strip()
            if output == 'true':
                return True
            elif output == 'false':
                return False

    @property
    def container_ids(self):
        output = self.execute(['ps', '-a', '-q'])
        return output.splitlines()

    @property
    def container_info(self):
        ids = self.container_ids

        if ids:
            params = ['inspect'] + ids
            output = self.execute(params)
            return json.loads(output)
        else:
            return []

    @property
    def basic_info(self):
        """
        Similar to container_info, but much simpler.
        """
        ret = []
        for cinfo in self.container_info:
            name = cinfo['Name'][1:]

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

            ret.append((name, state, bind_description_list))

        return ret

    def info_lines(self, project=None):

        def projectfilter(info):
            if project:
                name = info[0].split('.')
                if len(name) == 1:
                    return False
                if name[0] != project:
                    return False
            return True

        info = filter(projectfilter, self.basic_info)

        if info:
            max_name_len = max([len(x[0]) + 2 for x in info])
            max_state_len = max([len(x[1]) + 2 for x in info])
            all_bind_desc = sum([x[2] for x in info], [])
            max_bind_len = max([len(x) for x in all_bind_desc])

            # compensate when no bind info
            if max_bind_len == 0:
                max_bind_len = -2

            max_len = max_name_len + max_state_len + max_bind_len

            yield(('y', '-' * max_len))

            fmt = '{0:<%s}{1:<%s}{2}' % (max_name_len, max_state_len)

            for name, state, bind_description_list in info:
                message = fmt.format(name, state, bind_description_list[0])
                if state == 'running':
                    yield(('g', message))
                else:
                    yield(('e', message))

                for other in bind_description_list[1:]:
                    message = fmt.format('', '', other)
                    if state == 'running':
                        yield(('g', message))
                    else:
                        yield(('e', message))

            yield(('y', '-' * max_len))
