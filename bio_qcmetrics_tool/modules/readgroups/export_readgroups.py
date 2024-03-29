"""Extract readgroup information"""
import json
import os
import sqlite3

import pandas as pd

from bio_qcmetrics_tool.modules.base import ExportQcModule
from bio_qcmetrics_tool.modules.exceptions import DuplicateInputException


class ExportReadgroup(ExportQcModule):
    """Extract Readgroup metadata"""

    def __init__(self, options=dict()):
        super().__init__(name="readgroup", options=options)

    @classmethod
    def __add_arguments__(cls, subparser):
        subparser.add_argument(
            "-i",
            "--inputs",
            action="append",
            required=True,
            help="Input readgroup JSON files",
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
            help="The bam associated with the inputs.",
        )

    @classmethod
    def __get_description__(cls):
        return "Extract readgroup metadata"

    def do_work(self):
        super().do_work()

        self.logger.info(
            "Processing {0} readgroup files...".format(len(self.options["inputs"]))
        )

        for rgfile in self.options["inputs"]:
            basename = os.path.basename(rgfile)
            if basename in self.data:
                raise DuplicateInputException(
                    "Duplicate input files?? {0}".format(basename)
                )
            self.logger.info("Processing {0}".format(basename))
            self.data[basename] = dict()

            with open(rgfile, "rt") as fh:
                data = json.load(fh)
                self.data[basename]["readgroup"] = data

        # Export
        self.export()

    def to_sqlite(self):
        data = []
        for fil in sorted(self.data):
            rgid = self.data[fil]["readgroup"]["ID"]
            for key in sorted(self.data[fil]["readgroup"]):
                rec = {
                    "job_uuid": self.options["job_uuid"],
                    "bam": os.path.basename(self.options["bam"]),
                    "ID": rgid,
                    "key": key,
                    "value": self.data[fil]["readgroup"][key],
                }
                data.append(rec)

        self.logger.info(
            "Writing metrics to sqlite file {0}".format(self.options["output"])
        )

        if data:
            with sqlite3.connect(self.options["output"]) as conn:
                df = pd.DataFrame(data)
                table_name = "readgroups"
                df.to_sql(table_name, conn, if_exists="append")
