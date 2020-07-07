"""Tests for `bio_qcmetrics_tool.modules.readgroups`"""
import sqlite3
import tempfile
import unittest

from bio_qcmetrics_tool.modules.readgroups import ExportReadgroup
from tests.utils import cleanup_files, get_table_list, get_test_data_path


class TestExportReadgroup(unittest.TestCase):
    def test_init(self):
        opts = {}
        cls = ExportReadgroup(options=opts)
        self.assertEqual(cls.name, "readgroup")

    def test_do_work(self):
        (fd, fn) = tempfile.mkstemp()
        ifil = get_test_data_path("readgroups.json")
        jid = "fakeuuid"
        opts = {
            "inputs": [ifil],
            "export_format": "sqlite",
            "output": fn,
            "bam": "fake.bam",
            "job_uuid": jid,
        }
        exp_tables = set(["readgroups"])
        try:
            obj = ExportReadgroup(options=opts)
            obj.do_work()
            with sqlite3.connect(fn) as conn:
                cur = conn.cursor()
                tables = set(get_table_list(cur))
                self.assertEqual(tables, exp_tables)
        finally:
            cleanup_files(fn)
