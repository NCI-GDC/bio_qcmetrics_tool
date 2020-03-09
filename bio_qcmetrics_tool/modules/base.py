"""Module containing base classes for all modules"""
from abc import ABCMeta, abstractmethod

from bio_qcmetrics_tool.utils.logger import Logger


class Subcommand(metaclass=ABCMeta):
    """Base class of all subcommands modules."""

    def __init__(self, name=None, options=dict(), **kwargs):
        """
        Initialize with the name and command-line arguments dictionary.
        """
        self.logger = Logger.get_logger(self.__class__.__name__)
        self.name = name
        self.options = options
        self.data = dict()

        for key, value in kwargs.items():
            setattr(self, key, value)

    @abstractmethod
    def do_work(self):
        """
        Wrapper function used by CLI to process the data for this
        module.
        """
        self.logger.info(
            "{0} - {1}".format(
                self.__class__.__get_name__(), self.__class__.__get_description__()
            )
        )

    @classmethod
    @abstractmethod
    def __add_arguments__(cls, subparser):
        """
        Add arguments to a subparser.
        """

    @classmethod
    def __get_name__(cls):
        """
        Gets the name to use for the sub-parser
        """
        return cls.__name__.lower()

    @classmethod
    def __get_description__(cls):
        """
        Gets the description to use for the sub-parser
        """

    @classmethod
    def __from_subparser__(cls, options):
        """
        Entrypoint to initialize class from the options
        provided by the CLI argument parser.
        """
        return cls(options=vars(options))

    @classmethod
    def add(cls, subparsers):
        """Adds the given subcommand to the subprsers."""
        subparser = subparsers.add_parser(
            name=cls.__get_name__(), description=cls.__get_description__()
        )

        cls.__add_arguments__(subparser)
        subparser.set_defaults(func=cls.__from_subparser__)
        return subparser


class ExportQcModule(Subcommand):
    """Base class for CLI modules that take raw metrics files and
    export the data into a particular format."""

    @abstractmethod
    def to_sqlite(self):
        """
        Implement the exporting to sqlite db.
        """

    def export(self):
        """
        All tools must provide ability to export to various formats.
        """
        if self.options["export_format"] == "sqlite":
            return self.to_sqlite()
        else:
            raise NotImplementedError("Not implemented")

    @classmethod
    def exporters(cls):
        """
        The available export formats.
        """
        exporters = ["sqlite"]
        return exporters

    @classmethod
    def add(cls, subparsers):
        """Adds the given subcommand to the subprsers."""
        # I remove the "export" from __get_name__()
        subparser = subparsers.add_parser(
            name=cls.__get_name__().replace("export", ""),
            description=cls.__get_description__(),
        )

        cls.__add_arguments__(subparser)

        # All export tool include these options
        subparser.add_argument(
            "--export_format",
            choices=cls.exporters(),
            required=True,
            help="The available formats to export",
        )
        subparser.add_argument(
            "-o", "--output", required=True, help="The path to the output file"
        )

        subparser.set_defaults(func=cls.__from_subparser__)
        return subparser
