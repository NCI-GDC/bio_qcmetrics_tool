"""QC Module for Exporting samtools idxstats

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
import pandas as pd
import sqlite3

from bio_qcmetrics_tool.utils.parse import parse_type, get_read_func
from bio_qcmetrics_tool.modules.base import ExportQcModule
from bio_qcmetrics_tool.modules.exceptions import (
    DuplicateInputException,
    ParserException,
)


class ExportSamtoolsIdxstats(ExportQcModule):
    """Extract samtools idxstats"""

    def __init__(self, options=dict()):
        super().__init__(name="samtools idxstats", options=options)

    @classmethod
    def __add_arguments__(cls, subparser):
        subparser.add_argument(
            "-i",
            "--inputs",
            action="append",
            required=True,
            help="Input idxstats file. May be used one or more times",
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
        return "Extract samtools idxstats metrics."

    def do_work(self):
        super().do_work()

        self.logger.info(
            "Processing {0} idxstat files...".format(len(self.options["inputs"]))
        )

        for idxfile in self.options["inputs"]:
            basename = os.path.basename(idxfile)
            if basename in self.data:
                raise DuplicateInputException(
                    "Duplicate input files?? {0}".format(basename)
                )
            self.logger.info("Processing {0}".format(basename))
            self.data[basename] = dict()
            rfunc = get_read_func(idxfile)
            with rfunc(idxfile, "rt") as fh:
                self.data[basename]["idxstat"] = {
                    "bam": os.path.basename(self.options["bam"]),
                    "job_uuid": self.options["job_uuid"],
                    "colnames": ["NAME", "LENGTH", "ALIGNED_READS", "UNALIGNED_READS"],
                    "values": self._parse(fh),
                }

        # Export data
        self.export()

    def to_sqlite(self):
        data = []
        for source in sorted(self.data):
            record = self.data[source]["idxstat"]
            cols = record["colnames"]
            for row in record["values"]:
                curr = dict(zip(cols, row))
                curr["job_uuid"] = record["job_uuid"]
                curr["bam"] = record["bam"]
                curr["idxstat_file"] = source
                data.append(curr)

        if data:
            self.logger.info(
                "Writing metrics to sqlite file {0}".format(self.options["output"])
            )

            with sqlite3.connect(self.options["output"]) as conn:
                df = pd.DataFrame(data)
                table_name = "samtools_idxstat"
                df.to_sql(table_name, conn, if_exists="append")

    def _parse(self, fh):
        """
        Parse the idxstat data from the file handle object 
        """
        parsed_data = []
        for line in fh:
            cols = line.rstrip("\r\n").split("\t")
            if len(cols) != 4:
                raise ParserException(
                    "Unexpected column number on line: {0}".format(line.rstrip("\r\n"))
                )
            chrom = cols[0]
            vals = list([parse_type(i) for i in cols[1:]])
            row = [chrom] + vals
            parsed_data.append(row)
        return parsed_data
