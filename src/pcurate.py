"""pcurate

Usage:
  pcurate PACKAGE_NAME [-u | -s [-t TAG] [-d DESCRIPTION]]
  pcurate ( -c | -n | -m ) [-v]
  pcurate ( -h | --help | --version)

Options:
  -u --unset              Unset package curated status
  -s --set                Set package curated status
  -t tag --tag tag        Set package tag
  -d desc --desc desc     Set package description
  -c --curated            Display all curated packages
  -n --normal             Display packages not curated
  -m --missing            Display missing curated packages
  -v --verbose            Display additional info (csv)
  -h --help               Display help
  --version               Display pcurate version

"""

__version__ = '0.1.5'

# standard lib import
import os
import re
import sqlite3
import subprocess

# third party import
from docopt import docopt


class Package:
    """A class to store and retrieve info for Arch Linux software packages

    Attributes
    ----------
    name : str
        the name of the software package
    curated : int
        value of 1 marks package as a keeper (default 0)
    tag : str
        optional curated package tag (default None)
    description : str
        optional curated package desc (if None will use stock desc)
    """

    def __init__(self, name, curated=0, tag=None, description=None) -> None:
        """init package object representing Arch Linux software package

        Parameters
        ----------
        name : str
            the name of the software package
        curated : int
            value of 1 marks package as a keeper (default 0)
        tag : str
            optional for curated package categorization (default None)
        description : str
            optional curated package desc (if None will use stock desc)
        """

        self.name = name
        self.curated = curated
        self.tag = tag
        self.description = description

    def add(self, db) -> None:
        """takes db connect obj, adds a package and its attributes to db"""

        db.execute("""INSERT OR IGNORE INTO packages VALUES (:name,
                   :curated, :tag, :description)""", {
                   'name': self.name, 'curated': self.curated,
                   'tag': self.tag, 'description': self.description})

    def modify(self, db) -> None:
        """takes db connect obj, modifies attributes of a package in db"""

        db.execute("""UPDATE packages SET curated = ifnull(:curated,curated),
                   tag = ifnull(:tag,tag), description = ifnull(:description,
                   description) WHERE name = :name""", {
                   'name': self.name, 'curated': self.curated,
                   'tag': self.tag, 'description': self.description})

    def display(self, db) -> str:
        """takes db connect obj, displays attribs stored for package in db"""

        o = db.query('Select * FROM packages WHERE name = :name',
                     {'name': self.name})
        try:
            name, curated, tag, description = o[0]
            status = ',curated,' if curated == 1 else ',normal,'
            print(name + status + tag + "," + description)
            return o
        except IndexError:
            print("package not excplicitly installed (" + self.name + ")")
            return 'no_match'


class Database:
    """A class to handle a sqlite db of Arch linux software package info

    Attributes
    ----------
    conn
        database connection object
    cursor
        database cursor object
    """

    def __init__(self, db_path) -> None:
        """takes str path to db and initialize it, create it if not exist"""

        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS packages (name text PRIMARY KEY,
                            curated integer,tag text,description text)""")

    def __enter__(self) -> 'Database':
        """bind db instance to context manager"""

        return self

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        """called when context mgr leaves context, args are for exceptions"""

        self.close()

    def close(self, commit=True) -> None:
        """takes bool to toggle change commit (default True), and closes db"""

        if commit:
            self.conn.commit()
        self.conn.close()

    def execute(self, sql, params=None) -> None:
        """takes sql str w optional named placeholders"""

        self.cursor.execute(sql, params or ())

    def query(self, sql, params=None) -> list:
        """takes sql str w optional named placeholders and returns rows"""

        self.cursor.execute(sql, params or ())
        return self.cursor.fetchall()

    def repopulate(self) -> None:
        """clear and rebuild db entries for all packages not curated"""

        self.cursor.execute('DELETE FROM packages WHERE curated = 0')
        pkglist = subprocess.check_output(['pacman', '-Qei'])
        pkglist = pkglist.decode('utf-8')
        for line in pkglist.split('\n'):
            if re.search('^Name', line):
                _, name = line.split(': ', 1)
            elif re.search('^Description', line):
                _, description = line.split(': ', 1)
                pkg = Package(name, 0, '', description)
                pkg.add(self.cursor)

    def filter(self, filter_file) -> None:
        """takes filter file obj, filter pkg or pkg group members from db"""

        filters = ''
        for line in filter_file:
            filters += line
            # convert to whitespace separated for use as pacman args
            filters = filters.replace('\n', ' ')
            # apply specified package and package group filters
        grp_filter = subprocess.getstatusoutput('pacman -Sgq ' + filters)
        for name in grp_filter[1].split('\n') + filters.split(' '):
            self.execute("""DELETE FROM packages WHERE name = :name
                         and curated = 0""", {'name': name})

    def output(self, args) -> list:
        """takes dict of parsed CLI args, sends formatted db info to stdout"""

        if args['--verbose']:
            print("name, status, tag, description")
        o = self.query("""SELECT * FROM packages WHERE curated = :curated
                       ORDER BY name""", {'curated': args['--curated']})
        status = ',curated,' if args['--curated'] else ',normal,'
        for i in range(len(o)):
            if not args['--verbose']:
                print(o[i][0])
            else:
                print(o[i][0] + status + o[i][2] + ',"' + o[i][3] + '"')
        return o

    def missing(self, args) -> list:
        """takes dict of parsed CLI args, output list of missing curated"""

        if args['--verbose']:
            print("name, status, tag, description")
        o = self.query("""SELECT * FROM packages WHERE curated = 1
                       ORDER BY name""")
        pkglist = subprocess.check_output(['pacman', '-Qqe'])
        pkglist = pkglist.decode('utf-8')
        result = ''
        for i in range(len(o)):
            if o[i][0] not in pkglist.split('\n'):
                if not args['--verbose']:
                    print(o[i][0])
                else:
                    print(o[i][0] + ',curated,' + o[i][2]
                          + ',"' + o[i][3] + '"')
                result += o[i][0] + '\n'
        return result


class __Control:
    """A class to set up config and provide a simple control interface

    Attributes
    ----------
    config_path
        path to configuration directory
    db_path
        path to sqlite database file
    filter_path
        path to optional filter file
    """

    def __init__(self) -> None:
        """set up file paths; respect XDG_CONFIG_HOME if it exists"""

        xdg = os.environ.get('XDG_CONFIG_HOME')
        if not xdg:
            xdg = os.path.expandvars('$HOME') + '/.config'
        self.config_path = xdg + '/pcurate'
        os.makedirs(self.config_path, exist_ok=True)
        self.db_path = self.config_path + '/pcurate.db'
        self.filter_path = self.config_path + '/filter.txt'

    def output(self, args) -> None:
        """takes args, use to control package list output"""

        with Database(self.db_path) as db:
            self.filter(db)
            db.output(args)

    def missing(self, args) -> None:
        """takes args, use to control display of missing curated pkgs"""

        with Database(self.db_path) as db:
            db.missing(args)

    def display(self, args) -> None:
        """takes args, use to control pkg changes/display"""

        pkg = Package(args['PACKAGE_NAME'], args['--set'],
                      args['--tag'], args['--desc'])
        with Database(self.db_path) as db:
            db.repopulate()
            if args['--set'] or args['--unset']:
                pkg.modify(db)
                db.conn.commit()
            pkg.display(db)

    def filter(self, db) -> None:
        """takes db reference, use to control repopulate and filter of db"""

        db.repopulate()
        if os.path.isfile(self.filter_path):
            with open(self.filter_path, 'r') as filter_file:
                db.filter(filter_file)


def main() -> None:
    """dispatch commands based on CLI args parsed by docopt"""

    c = __Control()
    args = docopt(__doc__)
    if args['--curated'] or args['--normal']:
        c.output(args)
    elif args['--missing']:
        c.missing(args)
    elif args['PACKAGE_NAME']:
        c.display(args)
    elif args['--version']:
        print("pcurate version " + __version__)


if __name__ == '__main__':
    main()
