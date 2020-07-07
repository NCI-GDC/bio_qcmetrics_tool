"""QC Module for Exporting samtools stats

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
import sqlite3

import pandas as pd

from bio_qcmetrics_tool.modules.base import ExportQcModule
from bio_qcmetrics_tool.modules.exceptions import (
    DuplicateInputException,
    ParserException,
)
from bio_qcmetrics_tool.utils.parse import get_read_func, parse_type


class ExportSamtoolsStats(ExportQcModule):
    """Extract samtools stats"""

    def __init__(self, options=dict()):
        super().__init__(name="samtools stats", options=options)

    @classmethod
    def __add_arguments__(cls, subparser):
        subparser.add_argument("-i", "--input", required=True, help="Input stats file")

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
        return "Extract samtools stats metrics."

    def do_work(self):
        super().do_work()

        statfile = self.options["input"]
        basename = os.path.basename(statfile)
        self.logger.info("Processing {0}".format(basename))
        self.data = dict()
        rfunc = get_read_func(statfile)

        with rfunc(statfile, "rt") as fh:
            self.data["samtools_stats"] = {
                "bam": os.path.basename(self.options["bam"]),
                "job_uuid": self.options["job_uuid"],
                "data": self._parse_stats(fh),
            }

        # Export data
        self.export()

    def to_sqlite(self):
        data = {
            "bam": [self.data["samtools_stats"]["bam"]],
            "job_uuid": [self.data["samtools_stats"]["job_uuid"]],
            "samtools_stats_file": [os.path.basename(self.options["input"])],
        }
        for key in self.data["samtools_stats"]["data"]:
            data[key] = [self.data["samtools_stats"]["data"][key]]

        if data:
            self.logger.info(
                "Writing metrics to sqlite file {0}".format(self.options["output"])
            )
            with sqlite3.connect(self.options["output"]) as conn:
                df = pd.DataFrame(data)
                table_name = "samtools_stats"
                df.to_sql(table_name, conn, if_exists="append")

    def _parse_stats(self, fh):
        """
        Parse the stats data from the file handle
        """
        parsed_data = {}
        for line in fh:
            if line.startswith("SN\t"):
                cols = line.rstrip("\r\n").split("\t")
                key = (
                    cols[1]
                    .strip(":")
                    .replace(" ", "_")
                    .replace("(", "")
                    .replace(")", "")
                )
                try:
                    val = int(cols[2])
                except ValueError:
                    val = float(cols[2])
                parsed_data[key] = val

        return parsed_data
