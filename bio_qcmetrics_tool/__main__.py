"""Main entrypoint for all modules."""
import argparse
import importlib
import inspect
import pkgutil
import sys
from signal import SIG_DFL, SIGPIPE, signal

from bio_qcmetrics_tool.utils.logger import Logger

signal(SIGPIPE, SIG_DFL)


def main(args=None, extra_subparser=None):
    """
    Main wrapper function.
    """
    # Set up logger
    Logger.setup_root_logger()

    parser = argparse.ArgumentParser("bio_qcmetrics_tool")
    main_subparsers = parser.add_subparsers(dest="main_subcommand")
    main_subparsers.required = True

    add_export_tools(main_subparsers)

    options = parser.parse_args()
    cls = options.func(options)
    cls.do_work()


def add_export_tools(subparsers):
    """
    Dynamically load all export tools.
    """
    from bio_qcmetrics_tool.modules.base import ExportQcModule

    def predicate(obj):
        return inspect.isclass(obj) and issubclass(obj, ExportQcModule)

    export_parser = subparsers.add_parser(
        name="export", description="Export metrics files into a standardized format"
    )
    export_parser_sps = export_parser.add_subparsers(dest="subcommand")
    export_parser_sps.required = True
    mod = importlib.import_module("bio_qcmetrics_tool.modules")
    for p in pkgutil.walk_packages(mod.__path__, mod.__name__ + "."):
        if p[2]:
            curr = importlib.import_module(p[1])
            for m in inspect.getmembers(curr, predicate):
                m[1].add(subparsers=export_parser_sps)


if __name__ == "__main__":
    main()
