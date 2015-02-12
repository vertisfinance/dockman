# encoding: utf-8
import os

import pytest

from dockman import context
from dockman import docker
import dockman


cwd = os.path.dirname(__file__)
cwd1 = os.path.join(cwd, 'a')
cwd2 = os.path.join(cwd1, 'b')


def test_read_config():
    with pytest.raises(context.NoConfigException):
        context.Context(config_filename='dockman.yaml')

    with pytest.raises(context.WrongConfigException):
        context.Context(config_filename='test1.yaml',
                        path=cwd2)

    with pytest.raises(context.WrongConfigException):
        context.Context(config_filename='test2.yaml',
                        path=cwd1)

    with pytest.raises(context.WrongConfigException):
        context.Context(config_filename='test3.yaml',
                        path=cwd)

    with pytest.raises(context.WrongConfigException):
        context.Context(config_filename='test4.yaml',
                        path=cwd)

    with pytest.raises(context.WrongConfigException):
        context.Context(config_filename='test5.yaml',
                        path=cwd)

    ctx = context.Context(config_filename='test6.yaml',
                          path=cwd)

    assert ctx.containers.keys() == ['a', 'b']

    with pytest.raises(context.WrongConfigException):
        context.Context(config_filename='test7.yaml',
                        path=cwd)

    with pytest.raises(context.WrongConfigException):
        context.Context(config_filename='test8.yaml',
                        path=cwd)


def test_chains():
    ctx = context.Context(config_filename='test9.yaml',
                          path=cwd)

    a = ctx.containers['a']
    b = ctx.containers['b']
    c = ctx.containers['c']
    d = ctx.containers['d']
    e = ctx.containers['e']
    f = ctx.containers['f']

    assert ctx.dependencies(a) == set()
    assert ctx.dependencies(b) == set([a])
    assert ctx.dependencies(c) == set([a])
    assert ctx.dependencies(d) == set([b, c])
    assert ctx.dependencies(e) == set([b])
    assert ctx.dependencies(f) == set([d, e])

    assert ctx.reverse_dependencies(a) == set([b, c])
    assert ctx.reverse_dependencies(b) == set([d, e])
    assert ctx.reverse_dependencies(c) == set([d])
    assert ctx.reverse_dependencies(d) == set([f])
    assert ctx.reverse_dependencies(e) == set([f])
    assert ctx.reverse_dependencies(f) == set()

    assert ctx.chain(a) == [a]
    assert ctx.chain(b) == [a, b]
    assert ctx.chain(c) == [a, c]
    assert ctx.chain(d) in ([a, b, c, d], [a, c, b, d])
    assert ctx.chain(e) == [a, b, e]
    chain = ctx.chain(f)
    assert chain in ([a, b, c, e, d, f],
                     [a, b, c, d, e, f],
                     [a, b, e, c, d, f],
                     [a, c, b, e, d, f],
                     [a, c, b, d, e, f])

    assert ctx.reverse_chain(f) == [f]

    ctx = context.Context(config_filename='test10.yaml',
                          path=cwd)
    with pytest.raises(context.WrongConfigException) as e:
        ctx.chain(ctx.containers['f'])
    assert e.value.message in ('Circular dependencies: f -> e -> b -> a -> f',
                               'Circular dependencies: f -> d -> b -> a -> f',
                               'Circular dependencies: f -> d -> c -> a -> f')


def test_run(capsys):
    ctx = dockman.CONTEXT = context.Context(config_filename='test9.yaml',
                                            path=cwd)
    safedocker = dockman.DOCKER = docker.SafeDocker(_output=[Exception()])

    ctx.run(interactive=False, container_name='a', extra=[])

    out, _ = capsys.readouterr()
    assert out == u'test.a starting ... ✔\n'
    assert safedocker._cmd == ['docker', 'run', '-d', '--name', 'test.a',
                               '-e', 'container_name=test.a', 'a']
