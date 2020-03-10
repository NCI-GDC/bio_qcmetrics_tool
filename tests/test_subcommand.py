"""Tests the `bio_qcmetrics_tool.modules.base` `Subcommand` and
`ExportQcModule` classes
"""
import unittest
import attr
import argparse

from bio_qcmetrics_tool.modules.base import Subcommand, ExportQcModule

from utils import captured_output


@attr.s
class MockArgs(object):
    export_format = attr.ib(default="sqlite")


class TestSubcommand(unittest.TestCase):
    class Example(Subcommand):
        def do_work(self):
            pass

        @classmethod
        def __get_description__(cls):
            return "DESCRIPTION"

        @classmethod
        def __add_arguments__(cls, subparser):
            pass

    def test_get_name(self):
        self.assertEqual(TestSubcommand.Example.__get_name__(), "example")
        self.assertEqual(Subcommand.__get_name__(), "subcommand")

    def test_get_description(self):
        self.assertEqual(TestSubcommand.Example.__get_description__(), "DESCRIPTION")

    def test_init(self):
        opts = MockArgs()
        obj = TestSubcommand.Example(options=vars(opts))
        self.assertIsNone(obj.name)
        self.assertEqual(obj.options, vars(opts))

        obj = TestSubcommand.Example(name="TEST", options=vars(opts), other="HERE")
        self.assertEqual(obj.name, "TEST")
        self.assertTrue(hasattr(obj, "other"))
        self.assertEqual(obj.other, "HERE")

    def test_from_subparser(self):
        opts = MockArgs()
        obj = TestSubcommand.Example.__from_subparser__(opts)
        self.assertIsNone(obj.name)
        self.assertEqual(obj.options, vars(opts))


class TestExportQcModule(unittest.TestCase):
    class Example(ExportQcModule):
        def do_work(self):
            pass

        @classmethod
        def __add_argument__(cls, suparser):
            pass

        @classmethod
        def __get_description__(cls):
            return "DESCRIPTION"

    def test_exporters(self):
        self.assertEqual(TestExportQcModule.Example.exporters(), ["sqlite"])

    def test_add(self):
        parser = argparse.ArgumentParser()
        sp = parser.add_subparsers(dest="subcommand")
        TestExportQcModule.Example.add(subparsers=sp)
        with self.assertRaises(SystemExit), captured_output() as (_, _):
            opts = parser.parse_args(["example"])

    def test_add_full(self):
        parser = argparse.ArgumentParser()
        sp = parser.add_subparsers(dest="subcommand")
        TestExportQcModule.Example.add(subparsers=sp)
        with captured_output() as (_, stderr):
            opts = parser.parse_args(
                ["example", "--export_format", "sqlite", "-o", ":memory:"]
            )

        self.assertEqual(stderr.getvalue().rstrip("\r\n"), "")
