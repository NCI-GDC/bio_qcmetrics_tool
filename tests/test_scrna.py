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
        return {'Estimated_Number_of_Cells':['5,032'],
        'Mean_Reads_per_Cell':['76,300'],
        'Median_Genes_per_Cell':['2,214'],
        'Number_of_Reads':['383,941,607'],
        'Valid_Barcodes':['97.8%'],
        'Sequencing_Saturation':['75.2%'],
        'Q30_Bases_in_Barcode':['96.4%'],
        'Q30_Bases_in_RNA_Read':['95.4%'],
        'Q30_Bases_in_Sample_Index':['93.6%'],
        'Q30_Bases_in_UMI':['96.5%'],
        'Reads_Mapped_to_Genome':['97.1%'],
        'Reads_Mapped_Confidently_to_Genome':['91.5%'],
        'Reads_Mapped_Confidently_to_Intergenic_Regions':['4.1%'],
        'Reads_Mapped_Confidently_to_Intronic_Regions':['31.9%'],
        'Reads_Mapped_Confidently_to_Exonic_Regions':['55.5%'],
        'Reads_Mapped_Confidently_to_Transcriptome':['52.3%'],
        'Reads_Mapped_Antisense_to_Gene':['1.2%'],
        'Fraction_Reads_in_Cells':['94.1%'],
        'Total_Genes_Detected':['28,162'],
        'Median_UMI_Counts_per_Cell':['7,805']
        }

    def test_init(self):
        opts = {}
        cls = ExportTenXScrnaMetrics(options=opts)
        self.assertEqual(cls.name, "10x scrna flagstats")

    def test__parse_scrnametrics(self):
        obj = ExportTenXScrnaMetrics(options={})
        ifil = get_test_data_path("scrna.metrics.csv")
        rec = None
        with open(ifil, "rt") as fh:
            res = obj._parse_scrnametrics(ifil)
            exp = self.gen_fstats_expected()# set up
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
