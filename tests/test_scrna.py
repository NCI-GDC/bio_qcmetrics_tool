"""Tests for `bio_qcmetrics_tool.modules.samtools`"""
import unittest
import tempfile
import sqlite3
import math
import pandas as pd

from bio_qcmetrics_tool.modules.scrna import ExportTenXScrnaMetrics
from bio_qcmetrics_tool.modules.exceptions import ParserException

from utils import get_test_data_path, get_table_list, cleanup_files


class TestExportScrnaMetrics(unittest.TestCase):
    def gen_results(self):
        return {'estimated_number_of_cells': ['5032', '5034'],
        'mean_reads_per_cell': ['76300', '76300'],
        'median_genes_per_cell': ['2214', '2214'],
        'number_of_reads': ['383941607', '383941607'],
        'valid_barcodes': ['97.8', '97.8'],
        'sequencing_saturation': ['75.2', '75.2'],
        'q30_bases_in_barcode': ['96.4', '96.4'],
        'q30_bases_in_rna_read': ['95.4', '95.4'],
        'q30_bases_in_sample_index': ['93.6', '93.6'],
        'q30_bases_in_umi': ['96.5', '96.5'],
        'reads_mapped_to_genome': ['97.1', '97.1'],
        'reads_mapped_confidently_to_genome': ['91.5', '91.5'],
        'reads_mapped_confidently_to_intergenic_regions': ['4.1', '4.1'],
        'reads_mapped_confidently_to_intronic_regions': ['31.9', '31.9'],
        'reads_mapped_confidently_to_exonic_regions': ['55.5', '55.5'],
        'reads_mapped_confidently_to_transcriptome': ['52.3', '52.3'],
        'reads_mapped_antisense_to_gene': ['1.2', '1.2'],
        'fraction_reads_in_cells': ['94.1', '94.1'],
        'total_genes_detected': ['28162', '28162'],
        'median_umi_counts_per_cell': ['7805', '7805']}

    def test_init(self):
        opts = {}
        cls = ExportTenXScrnaMetrics(options=opts)
        self.assertEqual(cls.name, "10x scrna metrics")

    def test__parse_scrnametrics(self):
        obj = ExportTenXScrnaMetrics(options={})
        ifil = get_test_data_path("scrna.metrics.csv")
        rec = None
        with open(ifil, "r") as fh:
            res = obj._parse_scrnametrics(fh)
            exp = self.gen_results()
            self.assertDictEqual(res, exp)

    def test_do_work(self):
        (fd, fn) = tempfile.mkstemp()
        ifil = get_test_data_path("scrna.metrics.csv")
        jid = "fakeuuid"
        opts = {
            "inputs": [ifil],
            "export_format": "sqlite",
            "output": fn,
            "bam": "fake.bam",
            "job_uuid": jid,
        }
        exp_tables = set(["10x_scrna_metrics"])
        try:
            obj = ExportTenXScrnaMetrics(options=opts)
            obj.do_work()
            with sqlite3.connect(fn) as conn:
                cur = conn.cursor()
                tables = set(get_table_list(cur))
                self.assertEqual(tables, exp_tables)
        finally:
            cleanup_files(fn)
