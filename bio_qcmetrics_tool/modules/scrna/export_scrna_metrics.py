"""QC Module for Exporting 10x scrna metrics

Some of the file-parsing logic is adapted from:

    MultiQC: Summarize analysis results for multiple tools and samples in a single report
    Philip Ewels, Mans Magnusson, Sverker Lundin and Max Kaller
    Bioinformatics (2016)
    doi: 10.1093/bioinformatics/btw354
    PMID: 27312411
    https://github.com/ewels/MultiQC
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
        super().__init__(name="10x scrna flagstats", options=options)

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
            fsize = os.stat(scrnametricsfile).st_size
            if fsize > 5000:
                raise ParserException(
                    "Input file size '{0}' is larger than expected! Are you sure this is a 10x scrna metrics file?".format(
                        fsize
                    )
                )

            self.data[basename]["10x_scrna_metrics"] = {
                "bam": os.path.basename(self.options["bam"]),
                "job_uuid": self.options["job_uuid"],
                "data": self._parse_scrnametrics(),
                }

        # Export data
        self.export()

    def to_sqlite(self):
        data = []
        for source in sorted(self.data):
            record = self.data[source]["metrics"]
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

    def _parse_scrnametrics(self, fh):
        """
        Parse the 10x metrics data from the loaded file data
        """
        with open(scrnametricsfile, 'r') as csvfile:
          readcsv = list(csv.reader(csvfile))
          header = readcsv[0]
          headerfix = [item.replace(" ","_") for item in header]
          values = readcsv[1]
          metrics_dict = dict(zip(headerfix, values))
          parsed_data = pd.DataFrame(metrics_dict.items())
        return parsed_data
