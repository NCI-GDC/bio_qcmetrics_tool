"""Tests for `bio_qcmetrics_tool.modules.samtools`"""
import math
import sqlite3
import tempfile
import unittest

from bio_qcmetrics_tool.modules.exceptions import ParserException
from bio_qcmetrics_tool.modules.samtools import (
    ExportSamtoolsFlagstats,
    ExportSamtoolsIdxstats,
    ExportSamtoolsStats,
)
from tests.utils import cleanup_files, get_table_list, get_test_data_path


class TestExportSamtoolsFlagstats(unittest.TestCase):
    def gen_fstats_expected(self):
        return {
            "total": {"passed": 11540659, "failed": 0},
            "secondary": {"passed": 6365, "failed": 0},
            "supplementary": {"passed": 0, "failed": 0},
            "duplicates": {"passed": 0, "failed": 0},
            "mapped": {
                "passed": 11540643,
                "failed": 0,
                "passed_pct": 100.0,
                "failed_pct": float("nan"),
            },
            "paired in sequencing": {"passed": 11534294, "failed": 0},
            "read1": {"passed": 5767147, "failed": 0},
            "read2": {"passed": 5767147, "failed": 0},
            "properly paired": {
                "passed": 11518384,
                "failed": 0,
                "passed_pct": 99.86,
                "failed_pct": float("nan"),
            },
            "with itself and mate mapped": {"passed": 11534266, "failed": 0},
            "singletons": {
                "passed": 12,
                "failed": 0,
                "passed_pct": 0.0,
                "failed_pct": float("nan"),
            },
            "with mate mapped to a different chr": {"passed": 628, "failed": 0},
            "with mate mapped to a different chr (mapQ >= 5)": {
                "passed": 344,
                "failed": 0,
            },
        }

    def test_init(self):
        opts = {}
        cls = ExportSamtoolsFlagstats(options=opts)
        self.assertEqual(cls.name, "samtools flagstats")

    def test__parse_flagstat(self):
        obj = ExportSamtoolsFlagstats(options={})
        ifil = get_test_data_path("samtools.flagstat.log.txt")
        rec = None
        with open(ifil, "rt") as fh:
            rec = fh.read()
        res = obj._parse_flagstat(rec)
        exp = self.gen_fstats_expected()
        self.assertEqual(res.keys(), exp.keys())
        for key in exp:
            if res[key] != exp[key]:
                self.assertEqual(res[key].keys(), exp[key].keys())
                for item in res[key]:
                    if math.isnan(res[key][item]) and math.isnan(exp[key][item]):
                        continue
                    else:
                        self.assertEqual(res[key][item], exp[key][item])
            else:
                self.assertEqual(res[key], exp[key])

    def test_do_work(self):
        (fd, fn) = tempfile.mkstemp()
        ifil = get_test_data_path("samtools.flagstat.log.txt")
        jid = "fakeuuid"
        opts = {
            "inputs": [ifil],
            "export_format": "sqlite",
            "output": fn,
            "bam": "fake.bam",
            "job_uuid": jid,
        }
        exp_tables = set(["samtools_flagstat"])
        try:
            obj = ExportSamtoolsFlagstats(options=opts)
            obj.do_work()
            with sqlite3.connect(fn) as conn:
                cur = conn.cursor()
                tables = set(get_table_list(cur))
                self.assertEqual(tables, exp_tables)
        finally:
            cleanup_files(fn)


class TestExportSamtoolsIdxstats(unittest.TestCase):
    def test_init(self):
        opts = {}
        cls = ExportSamtoolsIdxstats(options=opts)
        self.assertEqual(cls.name, "samtools idxstats")

    def test__parse(self):
        obj = ExportSamtoolsIdxstats(options={})
        lines = ["1\t100\t100\t5", "2\t300\t10\t1"]
        exp = []
        for line in lines:
            curr = line.split("\t")
            curr = [curr[0]] + list(map(int, curr[1:]))
            exp.append(curr)
        res = obj._parse(lines)
        self.assertEqual(res, exp)

        lines = ["1\t100\t100\t5", "2\t300\t10\t1\t432423"]
        with self.assertRaises(ParserException):
            res = obj._parse(lines)

    def test_do_work(self):
        (fd, fn) = tempfile.mkstemp()
        ifil = get_test_data_path("samtools.idxstats.log.txt")
        jid = "fakeuuid"
        opts = {
            "inputs": [ifil],
            "export_format": "sqlite",
            "output": fn,
            "bam": "fake.bam",
            "job_uuid": jid,
        }
        exp_tables = set(["samtools_idxstat"])
        try:
            obj = ExportSamtoolsIdxstats(options=opts)
            obj.do_work()
            with sqlite3.connect(fn) as conn:
                cur = conn.cursor()
                tables = set(get_table_list(cur))
                self.assertEqual(tables, exp_tables)
        finally:
            cleanup_files(fn)


class TestExportExportSamtoolsStats(unittest.TestCase):
    def test_init(self):
        opts = {}
        cls = ExportSamtoolsStats(options=opts)
        self.assertEqual(cls.name, "samtools stats")

    def test__parse_stats(self):
        obj = ExportSamtoolsStats(options={})
        lines = [
            "#should skip",
            "SN\titem 1:\t1000",
            "SN\titem 2 (text):\t50",
            "SN\titem 3:\t100.2\t#some comment",
        ]
        exp = {"item_1": 1000, "item_2_text": 50, "item_3": 100.2}
        res = obj._parse_stats(lines)
        self.assertEqual(res, exp)

    def test_do_work(self):
        (fd, fn) = tempfile.mkstemp()
        ifil = get_test_data_path(
            "SRR1067503_1.fastq.gz_bowtie_srtd.bam_dedup.bam_samtools_stats.txt"
        )
        jid = "fakeuuid"
        opts = {
            "input": ifil,
            "export_format": "sqlite",
            "output": fn,
            "bam": "fake.bam",
            "job_uuid": jid,
        }
        exp_tables = set(["samtools_stats"])
        try:
            obj = ExportSamtoolsStats(options=opts)
            obj.do_work()
            with sqlite3.connect(fn) as conn:
                cur = conn.cursor()
                tables = set(get_table_list(cur))
                self.assertEqual(tables, exp_tables)
        finally:
            cleanup_files(fn)
