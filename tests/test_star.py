"""Tests for `bio_qcmetrics_tool.modules.star`"""
import sqlite3
import tempfile
import unittest

from bio_qcmetrics_tool.modules.star import ExportStarStats
from tests.utils import cleanup_files, get_table_list, get_test_data_path


class TestExportStarStats(unittest.TestCase):
    expected_log_json = {
        "total_reads": 94446403.0,
        "avg_input_read_length": 152.0,
        "uniquely_mapped": 75077194.0,
        "uniquely_mapped_percent": 79.49,
        "avg_mapped_read_length": 151.05,
        "num_splices": 12229052.0,
        "num_annotated_splices": 12092056.0,
        "num_GTAG_splices": 12123120.0,
        "num_GCAG_splices": 88078.0,
        "num_ATAC_splices": 10382.0,
        "num_noncanonical_splices": 7472.0,
        "mismatch_rate": 0.54,
        "deletion_rate": 0.01,
        "deletion_length": 1.3,
        "insertion_rate": 0.0,
        "insertion_length": 1.49,
        "multimapped": 4189751.0,
        "multimapped_percent": 4.44,
        "multimapped_toomany": 34465.0,
        "multimapped_toomany_percent": 0.04,
        "unmapped_mismatches_percent": 0.0,
        "unmapped_tooshort_percent": 16.01,
        "unmapped_other_percent": 0.02,
        "chimeric": 1343704.0,
        "chimeric_percent": 1.42,
        "unmapped_mismatches": 0,
        "unmapped_tooshort": 15126097,
        "unmapped_other": 18896,
    }

    expected_genecount_json = {
        "unstranded": {
            "N_genes": 21,
            "N_unmapped": 100,
            "N_multimapping": 200,
            "N_noFeature": 1000,
            "N_ambiguous": 100,
        },
        "first_strand": {
            "N_genes": 1,
            "N_unmapped": 100,
            "N_multimapping": 200,
            "N_noFeature": 5000,
            "N_ambiguous": 200,
        },
        "second_strand": {
            "N_genes": 26,
            "N_unmapped": 100,
            "N_multimapping": 200,
            "N_noFeature": 1200,
            "N_ambiguous": 100,
        },
    }

    def test_init(self):
        opts = {}
        cls = ExportStarStats(options=opts)
        self.assertEqual(cls.name, "star")

    def test_parse_star_final_log(self):
        ifil = get_test_data_path("star.log.final.out")
        jid = "fakeuuid"
        opts = {
            "final_log_inputs": [ifil],
            "export_format": "sqlite",
            "output": "fake.out",
            "bam": "fake.bam",
            "job_uuid": jid,
        }
        obj = ExportStarStats(options=opts)
        res = obj.parse_star_final_log(ifil)
        self.assertEqual(res, TestExportStarStats.expected_log_json)

    def test_parse_genecount_report(self):
        ifil = get_test_data_path("test_star_counts.txt")
        jid = "fakeuuid"
        opts = {
            "gene_counts_inputs": [ifil],
            "export_format": "sqlite",
            "output": "fake.out",
            "bam": "fake.bam",
            "job_uuid": jid,
        }
        obj = ExportStarStats(options=opts)
        res = obj.parse_star_genecount_report(ifil)
        self.assertEqual(res, TestExportStarStats.expected_genecount_json)

    def test_do_work(self):
        (fd, fn) = tempfile.mkstemp()
        ilog = get_test_data_path("star.log.final.out")
        icts = get_test_data_path("test_star_counts.txt")
        jid = "fakeuuid"
        opts = {
            "final_log_inputs": [ilog],
            "gene_counts_inputs": [icts],
            "export_format": "sqlite",
            "output": fn,
            "bam": "fake.bam",
            "job_uuid": jid,
        }
        exp_tables = set(["star_stats", "star_gene_counts"])
        try:
            obj = ExportStarStats(options=opts)
            obj.do_work()
            with sqlite3.connect(fn) as conn:
                cur = conn.cursor()
                tables = set(get_table_list(cur))
                self.assertEqual(tables, exp_tables)
        finally:
            cleanup_files(fn)
