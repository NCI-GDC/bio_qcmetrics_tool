"""Tests for `bio_qcmetrics_tool.modules.fastqc`"""
import unittest
import attr

from bio_qcmetrics_tool.modules.fastqc import ExportFastqc

from utils import captured_output


@attr.s
class MockZipFile(object):
    flist = attr.ib(factory=list)

    def namelist(self):
        if self.flist:
            return self.flist
        else:
            return ["fastqc_data.txt", "summary.txt", "other.txt"]


class TestExportFastqc(unittest.TestCase):
    def test_init(self):
        opts = {}
        cls = ExportFastqc(options=opts)
        self.assertEqual(cls.name, "fastqc")

    def test_get_fastqc_file_names(self):
        obj = ExportFastqc()
        zobj = MockZipFile()
        data_file, summary_file = obj.get_fastqc_file_names(zobj)
        self.assertEqual(data_file, "fastqc_data.txt")
        self.assertEqual(summary_file, "summary.txt")

        zobj = MockZipFile(["nothing"])
        with self.assertRaises(AssertionError):
            data_file, summary_file = obj.get_fastqc_file_names(zobj)

        zobj = MockZipFile(["nothing", "fastqc_data.txt"])
        with self.assertRaises(AssertionError):
            data_file, summary_file = obj.get_fastqc_file_names(zobj)

    def test_get_fastq_name(self):
        lines = [
            "blah blah".encode("utf-8"),
            "Filename\tfastq_file.fq.gz".encode("utf-8"),
        ]
        obj = ExportFastqc()
        res = obj.get_fastq_name(lines)
        self.assertEqual(res, "fastq_file.fq.gz")

    def test_parse_fastqc_summary(self):
        src = "fake"
        fq = "fastq_file_fq.gz"
        jid = "fakeuuid"
        obj = ExportFastqc(options={"job_uuid": jid})
        obj.data[src] = {}
        lines = [
            "PASS\ttest_cat\t{0}".format(fq).encode("utf-8"),
        ]
        obj.parse_fastqc_summary(src, fq, lines)
        self.assertTrue(src in obj.data)
        self.assertTrue("fastqc_summary" in obj.data[src])
        self.assertEqual(obj.data[src]["fastqc_summary"]["fastq"], fq)
        self.assertEqual(obj.data[src]["fastqc_summary"]["job_uuid"], jid)
        self.assertEqual(obj.data[src]["fastqc_summary"]["test_cat"], "PASS")
        self.assertIsNone(obj.data[src]["fastqc_summary"]["Per tile sequence quality"])

    def test__fastqc_data_section_generator(self):
        lines = ["##".encode("utf-8"), ">>END_MODULE".encode("utf-8")]
        jid = "fakeuuid"
        obj = ExportFastqc(options={"job_uuid": jid})
        gen = obj._fastqc_data_section_generator(lines)
        section, state, header, extra, data = next(gen)
        self.assertIsNone(section)
        self.assertIsNone(state)
        self.assertIsNone(header)
        self.assertIsNone(extra)
        self.assertEqual(data, [])

        lines = [
            "##".encode("utf-8"),
            ">>SECTION TEST\tFAIL".encode("utf-8"),
            ">>END_MODULE".encode("utf-8"),
        ]
        gen = obj._fastqc_data_section_generator(lines)
        section, state, header, extra, data = next(gen)
        self.assertEqual(section, "SECTION_TEST")
        self.assertEqual(state, "FAIL")
        self.assertIsNone(header)
        self.assertIsNone(extra)
        self.assertEqual(data, [])

        lines = [
            "##".encode("utf-8"),
            ">>SECTION TEST\tFAIL".encode("utf-8"),
            "#Total Deduplicated Percentage\t30.2".encode("utf-8"),
            "#colA\tcolB".encode("utf-8"),
            "A\tB".encode("utf-8"),
            ">>END_MODULE".encode("utf-8"),
            ">>SECTION TEST2\tWARN".encode("utf-8"),
            ">>END_MODULE".encode("utf-8"),
        ]
        gen = obj._fastqc_data_section_generator(lines)
        section, state, header, extra, data = next(gen)
        self.assertEqual(section, "SECTION_TEST")
        self.assertEqual(state, "FAIL")
        self.assertEqual(header, ["colA", "colB"])
        self.assertEqual(extra, "30.2")
        self.assertEqual(data, [["A", "B"]])

        section, state, header, extra, data = next(gen)
        self.assertEqual(section, "SECTION_TEST2")
        self.assertEqual(state, "WARN")
        self.assertIsNone(header)
        self.assertIsNone(extra)
        self.assertEqual(data, [])

    def test_parse_fastqc_data(self):
        lines = [
            "##".encode("utf-8"),
            ">>Basic Statistics\tPASS".encode("utf-8"),
            "#Measure\tValue".encode("utf-8"),
            "Total\t100".encode("utf-8"),
            ">>END_MODULE".encode("utf-8"),
            ">>Sequence duplication levels\tFAIL".encode("utf-8"),
            "#Total Deduplicated Percentage\t30.2".encode("utf-8"),
            "#colA\tcolB".encode("utf-8"),
            "A\tB".encode("utf-8"),
            ">>END_MODULE".encode("utf-8"),
            ">>SECTION TEST2\tWARN".encode("utf-8"),
            ">>END_MODULE".encode("utf-8"),
        ]
        src = "fake"
        fq = "fastq_file_fq.gz"
        jid = "fakeuuid"
        obj = ExportFastqc(options={"job_uuid": jid})
        obj.data[src] = {}
        obj.parse_fastqc_data(src, fq, lines)
        exp_dict = {
            "fake": {
                "Basic_Statistics": {
                    "fastq": "fastq_file_fq.gz",
                    "job_uuid": "fakeuuid",
                    "data": {"Total": 100, "Total Deduplicated Percentage": 30.2},
                },
                "Sequence_duplication_levels": {
                    "fastq": "fastq_file_fq.gz",
                    "job_uuid": "fakeuuid",
                    "data": [["A", "B"]],
                    "colnames": ["colA", "colB"],
                },
                "SECTION_TEST2": {
                    "fastq": "fastq_file_fq.gz",
                    "job_uuid": "fakeuuid",
                    "data": [],
                },
            }
        }
        self.assertEqual(obj.data, exp_dict)
