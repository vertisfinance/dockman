# coding: utf-8

from __future__ import absolute_import

import subprocess
import json
import threading
import Queue

from . import utils
import dockman


class DockerError(Exception):
    pass


class LogsThread(threading.Thread):
    def __init__(self, queue, command, container_name, **kwargs):
        super(LogsThread, self).__init__(**kwargs)
        self.queue = queue
        self.command = command
        self.container_name = container_name
        self.sp = None

    def run(self):
        fix_cmd = ['logs', '-f', '--tail="0"', self.container_name]
        self.sp = dockman.DOCKER.Popen(self.command + fix_cmd,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)

        while True:
            line = self.sp.stdout.readline()
            if not line:
                break

            self.queue.put((self.container_name, line), True, 0.1)

        self.sp.wait()

    def stop(self):
        if self.sp and self.sp.poll() is None:
            try:
                self.sp.terminate()
            except OSError:
                pass


class Docker(object):
    def __init__(self, command=['docker']):
        self.command = command
        self.logthreads = set()
        self.queue = Queue.Queue()

    def Popen(self, *args, **kwargs):
        return subprocess.Popen(*args, **kwargs)

    def execute(self, params):
        cmd = self.command + params

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise DockerError(e.output)
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
        self.execute(['rm', '-v', container_name])

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
                container_port = container_port.split('/')[0]
                for bind_item in bind_list or []:
                    desc = '%s -> %s:%s' % (container_port,
                                            bind_item['HostIp'],
                                            bind_item['HostPort'])
                    bind_description_list.append(desc)
            if not bind_description_list:
                bind_description_list = ['']

            ret.append((name, state, bind_description_list))

        return ret

    def running_container_names(self, project=None):

        def _filter(info):
            if info[1] != 'running':
                return False
            if project:
                name = info[0].split('.')
                if len(name) == 1:
                    return False
                if name[0] != project:
                    return False
            return True

        return [c[0] for c in filter(_filter, self.basic_info)]

    def ps(self, project=None):

        def projectfilter(info):
            if project:
                name = info[0].split('.')
                if len(name) == 1:
                    return False
                if name[0] != project:
                    return False
            return True

        info = filter(projectfilter, self.basic_info)
        if project:
            caption = 'Showing containers in project "%s"' % project
        else:
            caption = 'Showing all containers'

        if info:
            max_name_len = max([len(x[0]) + 2 for x in info])
            max_state_len = max([len(x[1]) + 2 for x in info])
            all_bind_desc = sum([x[2] for x in info], [])
            max_bind_len = max([len(x) for x in all_bind_desc])

            # compensate when no bind info
            if max_bind_len == 0:
                max_state_len -= 2

            max_len = max_name_len + max_state_len + max_bind_len
            max_len = max(max_len, len(caption))

            utils.yellow('-' * max_len)
            utils.echo(caption)
            utils.yellow('-' * max_len)

            fmt = '{0:<%s}{1:<%s}{2}' % (max_name_len, max_state_len)

            for name, state, bind_description_list in info:
                message = fmt.format(name, state, bind_description_list[0])
                if state == 'running':
                    utils.green(message)
                else:
                    utils.echo(message)

                for other in bind_description_list[1:]:
                    message = fmt.format('', '', other)
                    utils.green(message)

            utils.yellow('-' * max_len)

    def logs(self, container_names, max_iter=0):
        for cn in container_names:
            th = LogsThread(self.queue, self.command, cn)
            self.logthreads.add(th)
            th.start()

        iter_cnt = 0
        while (max_iter == 0) or (iter_cnt < max_iter):
            try:
                container_name, line = self.queue.get(True, 0.1)
            except Queue.Empty:
                continue
            else:
                self.queue.task_done()
                utils.yellow_(container_name + ': ')
                utils.echo_(line)
            finally:
                iter_cnt += 1

    def stopthreads(self):
        for th in self.logthreads:
            th.stop()
            th.join()


class SafeDocker(Docker):
    """
    Will not call subprocess, just remember the arguments.
    """
    def replace_with_content(self, o):
        if hasattr(o, 'read'):
                ret = o.read()
                o.close()
                return ret
        return o

    def __init__(self, *args, **kwargs):
        self._cmd = None
        self._output = None
        self._popenout_filename = None
        self._raise_oserror = False
        self._log_max_iter = 0

        if '_output' in kwargs:
            o = kwargs.pop('_output')
            if not hasattr(o, 'pop'):
                o = [o]
            self._output = map(self.replace_with_content, o)

        if '_popenout_filename' in kwargs:
            self._popenout_filename = kwargs.pop('_popenout_filename')

        if '_raise_oserror' in kwargs:
            self._raise_oserror = kwargs.pop('_raise_oserror')

        if '_log_max_iter' in kwargs:
            self._log_max_iter = kwargs.pop('_log_max_iter')

        super(SafeDocker, self).__init__(*args, **kwargs)

    def Popen(self, cmd, *args, **kwargs):

        _raise_oserror = self._raise_oserror

        class Dummy(object):
            def wait(self):
                pass

            def poll(self):
                pass

            def terminate(self):
                if _raise_oserror:
                    raise OSError()

        dp = Dummy()
        filename = self._popenout_filename + cmd[-1]
        dp.stdout = open(filename, 'r')
        return dp

    def execute(self, params):
        self._cmd = self.command + params

        if self._output:
            actual = self._output.pop(0)
            if isinstance(actual, Exception):
                raise actual
            else:
                return actual

    def execute_interactive(self, params):
        self._cmd = self.command + params

    def logs(self, container_names, max_iter=0):
        max_iter = max_iter or self._log_max_iter
        super(SafeDocker, self).logs(container_names, max_iter)
