from dockman.container import Container


def test_dependencies():
    config = {'image': 'foo_image',
              'volumes_from': ['shared'],
              'links': {'postgres': 'db'}}

    c = Container('foo', 'bar_project', config)
    assert c.dependencies == set(['shared', 'postgres'])
