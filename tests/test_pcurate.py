"""Test pcurate module with pytest."""

# standard lib import
import io

# third party import
import pytest
from pcurate import Database, Package


@pytest.fixture
def db():
    """Init a new in-memory db for each test function."""
    db = Database(':memory:')
    yield db
    db.close()


class __Control:
    """A class for a simple test control interface; wrapper functions.

    Attributes
    ----------
    name : db
        db connect obj
    """

    def __init__(self, db) -> None:
        """Take db connect obj."""
        self.db = db

    def display(self, pkg, repopulate=True) -> str:
        """Take pkg ojb, bool to toggle repop; controls pkg changes/display."""
        # optional bypass can be used to prevent resetting regular test entries
        if repopulate:
            self.db.repopulate()
        return pkg.display(self.db)

    def output(self, args) -> list:
        """Take dict of simulated args; controls package list output."""
        self.db.repopulate()
        return self.db.output(args)

    def filter(self, pkgnames) -> None:
        """Take filter text; control to apply filter using in memory obj."""
        with io.StringIO(pkgnames) as filter_file:
            self.db.filter(filter_file)


def test_package_set(db) -> None:
    """Test setting a package as curated status."""
    c = __Control(db)
    # add native test_package to db as a curated package with tag and desc
    pkg = Package('test_package', 1, 'test_tag', 'test_description', 1)
    pkg.add(db)
    # output of package data from package display function
    o = c.display(pkg)
    name, curated, tag, description, native = o[0]
    assert name == 'test_package'
    assert curated == 1
    assert tag == 'test_tag'
    assert description == 'test_description'
    assert native == 1
    # package name in curated package list output modes
    o = c.output({'--curated': True, '--verbose': False,
                  '--native': False, '--foreign': False})
    name = o[0][0]
    assert name == 'test_package'
    o = c.output({'--curated': True, '--verbose': True,
                  '--native': False, '--foreign': False})
    name, curated, tag, description, native = o[0]
    assert name == 'test_package'
    assert curated == 1
    assert tag == 'test_tag'
    assert description == 'test_description'
    assert native == 1


def test_package_modify(db) -> None:
    """Test modifications of curated package data."""
    c = __Control(db)
    # add test_package to db as a curated package with attributes
    pkg = Package('test_package', 1, 'test_tag', 'test_description', 0)
    pkg.add(db)
    # modify test package with new attributes and test display
    pkg = Package('test_package', 1, 'new_tag', 'new_description', 1)
    pkg.modify(db)
    name, curated, tag, description, native = c.display(pkg)[0]
    assert tag == 'new_tag'
    assert description == 'new_description'
    # check same test package attributes also in curated verbose output
    o = c.output({'--curated': True, '--verbose': True,
                  '--native': False, '--foreign': False})
    name, curated, tag, description, native = o[0]
    assert tag == 'new_tag'
    assert description == 'new_description'
    assert native == 1
    # unset the test package
    pkg = Package('test_package', 0, None, None)
    pkg.modify(db)
    o = c.display(pkg)
    assert o == 'no_match'


def test_regular_list(db) -> None:
    """Check to make sure regular database output has some content."""
    c = __Control(db)
    # regular output should have a number of rows after repopulating
    o = c.output({'--curated': False, '--regular': True, '--verbose': False,
                  '--native': False, '--foreign': False})
    assert len(o) > 5
    o = c.output({'--curated': False, '--regular': True, '--verbose': True,
                  '--native': False, '--foreign': False})
    assert len(o) > 5
    # 5 columns should be returned for entries in regular verbose output
    assert len(o[0]) == 5


def test_filtering(db) -> None:
    """Test filter processing, using the in-memory file object."""
    c = __Control(db)
    # add 3 test packages, and filter 2 of them
    pkg = Package('filter_one', 0, 'test_tag', 'test_description', 1)
    pkg.add(db)
    pkg = Package('filter_two', 0, 'test_tag', 'test_description', 1)
    pkg.add(db)
    pkg = Package('filter_three', 0, 'test_tag', 'test_description', 1)
    pkg.add(db)
    c.filter('filter_one\nfilter_three')
    o = c.display(pkg, False)
    assert o == 'no_match'
    pkg = Package('filter_two', 0, 'test_tag', 'test_description', 1)
    o = c.display(pkg, False)
    assert o != 'no_match'
    pkg = Package('filter_one', 0, 'test_tag', 'test_description', 1)
    o = c.display(pkg, False)
    assert o == 'no_match'


def test_missing(db) -> None:
    """Test detection of missing curated packages."""
    # add curated test package
    pkg = Package('test_package', 1, 'test_tag', 'test_description', 1)
    pkg.add(db)
    pkg = Package('base', 1, 'test_tag', 'test_description', 1)
    pkg.add(db)
    m = db.missing({'--verbose': False})
    # test_package is not actually installed so should report missing
    assert 'test_package' in m.split('\n')
    # base package should be installed so should not report missing
    assert 'base' not in m.split('\n')
