"""QC Module for Exporting 10x scrna metrics
@author Lauren Mogil <lmogil@uchicag.edu>
"""
import json
import os
import re
import pandas as pd
import sqlite3
import csv
from bio_qcmetrics_tool.utils.parse import parse_type, get_read_func
from bio_qcmetrics_tool.modules.base import ExportQcModule
from bio_qcmetrics_tool.modules.exceptions import (
    DuplicateInputException,
    ParserException,
)


class ExportTenXScrnaMetrics(ExportQcModule):
    """Extract 10x scrna metrics"""

    def __init__(self, options=dict()):
        super().__init__(name="10x scrna metrics", options=options)

    @classmethod
    def __add_arguments__(cls, subparser):
        subparser.add_argument(
            "-i",
            "--inputs",
            action="append",
            required=True,
            help="Input metrics file. May be used one or more times",
        )

        subparser.add_argument(
            "-j",
            "--job_uuid",
            type=str,
            required=True,
            help="The job uuid associated with the inputs.",
        )

        subparser.add_argument(
            "-b",
            "--bam",
            type=str,
            required=True,
            help="The bam that the metrics were derived from.",
        )

    @classmethod
    def __get_description__(cls):
        return "Extract 10x scrna metrics."
    def do_work(self):
        super().do_work()

        self.logger.info(
            "Processing {0} 10x scrna metrics files...".format(len(self.options["inputs"]))
        )

        for scrnametricsfile in self.options["inputs"]:
            basename = os.path.basename(scrnametricsfile)
            if basename in self.data:
                raise DuplicateInputException(
                    "Duplicate input files?? {0}".format(basename)
                )
            self.logger.info("Processing {0}".format(basename))
            self.data[basename] = dict()
            with open(scrnametricsfile, 'r') as csvfile:
                self.data[basename]["10x_scrna_metrics"] = {
                    "bam": os.path.basename(self.options["bam"]),
                    "job_uuid": self.options["job_uuid"],
                    "data": self._parse_scrnametrics(csvfile),
                    }
        # Export data
        self.export()

    def to_sqlite(self):
        data = []
        for source in sorted(self.data):
            record = self.data[source]["10x_scrna_metrics"]
            for section in sorted(record["data"]):
                curr = {
                    "job_uuid": record["job_uuid"],
                    "bam": record["bam"],
                    "metrics_file": source,
                    "category": section,

                }
                data.append(curr)

        if data:
            self.logger.info(
                "Writing metrics to sqlite file {0}".format(self.options["output"])
            )

            with sqlite3.connect(self.options["output"]) as conn:
                df = pd.DataFrame(data)
                table_name = "10x_scrna_metrics"
                df.to_sql(table_name, conn, if_exists="append")

    def _parse_scrnametrics(self,csvfile):
        """
        Parse the 10x metrics data from the loaded file data
        """
        expected_headers = ['estimated_number_of_cells', 'mean_reads_per_cell',
         'median_genes_per_cell', 'number_of_reads', 'valid_barcodes',
         'sequencing_saturation', 'q30_bases_in_barcode', 'q30_bases_in_rna_read',
         'q30_bases_in_sample_index', 'q30_bases_in_umi', 'reads_mapped_to_genome',
         'reads_mapped_confidently_to_genome', 'reads_mapped_confidently_to_intergenic_regions',
         'reads_mapped_confidently_to_intronic_regions', 'reads_mapped_confidently_to_exonic_regions',
         'reads_mapped_confidently_to_transcriptome', 'reads_mapped_antisense_to_gene',
         'fraction_reads_in_cells', 'total_genes_detected', 'median_umi_counts_per_cell']
        readcsv = csv.reader(csvfile)
        header = [item.replace(" ","_").lower() for item in next(readcsv)]
        for h in expected_headers:
            if h not in header:
                raise ParserException("File header is incorrect. Check file.")
        parsed_data = dict()
        for row in readcsv:
            rowfix = [r.replace("%","").replace(",","") for r in row]
            for head, *value in zip(header, rowfix):
                if head not in parsed_data:
                    parsed_data[head]=value
                else:
                    parsed_data[head].append("".join(value))
        return parsed_data
