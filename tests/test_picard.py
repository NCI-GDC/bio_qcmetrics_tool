"""Tests for `bio_qcmetrics_tool.modules.picard`"""
import unittest
import tempfile
import sqlite3
import os

from bio_qcmetrics_tool.modules.picard import ExportPicardMetrics
from bio_qcmetrics_tool.modules.picard.codec import PicardMetricsFile 
from bio_qcmetrics_tool.modules.picard.metrics.base import PICARD_METRICS_OBJECTS, PicardMetric

from utils import captured_output, get_test_data_path, get_table_list, cleanup_files


class TestPicardMetricsFile(unittest.TestCase):
    def test_init(self):
        cls = PicardMetricsFile('/path/fake.txt', headers=['fake'])
        self.assertEqual(cls.fpath, "/path/fake.txt")
        self.assertIsNone(cls.tool)
        self.assertEqual(cls.headers, ['fake'])
        self.assertIsNone(cls.metrics)

    def test_parsing(self):
        from bio_qcmetrics_tool.modules.picard.metrics.RnaSeqMetrics import RnaSeqMetrics
        ifil = get_test_data_path("CTC-1-AA-B2.star.bam.rnaseqmetrics.txt")
        obj = PicardMetricsFile(ifil)
        self.assertTrue(isinstance(obj.metrics, RnaSeqMetrics))


class TestPicardMetric(unittest.TestCase):
    class ExampleMetrics(PicardMetric):
        picard_tool_name = "FAKE"

        def __init__(self, source, histogram, field_names=None, values=None):
            super().__init__(
                class_name="ExampleMetrics",
                derived_from_key="bam",
                source=source,
                field_names=field_names,
                values=values,
                histogram=histogram,
            )
            
        @classmethod
        def from_picard_file_instance(cls, obj):
            pass

        @staticmethod
        def codec_match(some_bool):
            return some_bool
 
    def test_picard_metrics_objects_list(self):
        self.assertTrue(all([issubclass(i, PicardMetric) for i in PICARD_METRICS_OBJECTS]))

    def test_init(self):
        obj = TestPicardMetric.ExampleMetrics('src', None)
        self.assertEqual(obj.class_name, "ExampleMetrics")
        self.assertEqual(obj.source, 'src')
        self.assertEqual(obj.field_names, [])
        self.assertEqual(obj.values, [])
        self.assertIsNone(obj.histogram)
        self.assertEqual(obj.derived_from_key, "bam")

    def test_codec_match(self):
        self.assertTrue(TestPicardMetric.ExampleMetrics.codec_match(True))
        self.assertFalse(TestPicardMetric.ExampleMetrics.codec_match(False))

class TestExportPicardMetrics(unittest.TestCase):
    def test_init(self):
        opts = {}
        cls = ExportPicardMetrics(options=opts)
        self.assertEqual(cls.name, "picard")

    def test_do_work(self):
        (fd, fn) = tempfile.mkstemp()
        ifil = get_test_data_path("CTC-1-AA-B2.star.bam.rnaseqmetrics.txt")
        jid = "fakeuuid"
        opts = {
            "inputs": [ifil],
            "export_format": "sqlite",
            "output": fn,
            "derived_from_file": "bam",
            "job_uuid": jid 
        }
        try:
            obj = ExportPicardMetrics(options=opts)
            obj.do_work()
            self.assertTrue(os.path.isfile(fn))
            res = os.stat(fn)
            self.assertTrue(res.st_size > 1000)
            with sqlite3.connect(fn) as conn:
                pass
        finally:
            cleanup_files(fn)


class TestConcreteMetrics(unittest.TestCase):
    def test_rnaseq(self):
        (fd, fn) = tempfile.mkstemp()
        ifil = get_test_data_path("CTC-1-AA-B2.star.bam.rnaseqmetrics.txt")
        jid = "fakeuuid"
        opts = {
            "inputs": [ifil],
            "export_format": "sqlite",
            "output": fn,
            "derived_from_file": "bam",
            "job_uuid": jid 
        }
        exp_tables = set(["picard_RnaSeqMetrics", "picard_RnaSeqMetrics_histogram"])
        try:
            obj = ExportPicardMetrics(options=opts)
            obj.do_work()
            with sqlite3.connect(fn) as conn:
                cur = conn.cursor()
                tbls = set(get_table_list(cur)) 
                self.assertEqual(tbls, exp_tables)
        finally:
            cleanup_files(fn)

    def test_quality_by_cycle(self):
        (fd, fn) = tempfile.mkstemp()
        ifil = get_test_data_path("A1.sorted.dup.recal.all.metrics.quality_by_cycle_metrics")
        jid = "fakeuuid"
        opts = {
            "inputs": [ifil],
            "export_format": "sqlite",
            "output": fn,
            "derived_from_file": "bam",
            "job_uuid": jid 
        }
        exp_tables = set(["picard_QualityByCycleMetrics_histogram"])
        try:
            obj = ExportPicardMetrics(options=opts)
            obj.do_work()
            with sqlite3.connect(fn) as conn:
                cur = conn.cursor()
                tbls = set(get_table_list(cur)) 
                self.assertEqual(tbls, exp_tables)
        finally:
            cleanup_files(fn)

    def test_quality_distribution(self):
        (fd, fn) = tempfile.mkstemp()
        ifil = get_test_data_path("A1.sorted.dup.recal.all.metrics.quality_distribution_metrics")
        jid = "fakeuuid"
        opts = {
            "inputs": [ifil],
            "export_format": "sqlite",
            "output": fn,
            "derived_from_file": "bam",
            "job_uuid": jid 
        }
        exp_tables = set(["picard_QualityDistributionMetrics_histogram"])
        try:
            obj = ExportPicardMetrics(options=opts)
            obj.do_work()
            with sqlite3.connect(fn) as conn:
                cur = conn.cursor()
                tbls = set(get_table_list(cur)) 
                self.assertEqual(tbls, exp_tables)
        finally:
            cleanup_files(fn)
