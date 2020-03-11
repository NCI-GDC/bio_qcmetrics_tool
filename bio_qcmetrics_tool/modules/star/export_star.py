"""Export raw STAR stats into various formats

Some of the file-parsing logic is adapted from:

    MultiQC: Summarize analysis results for multiple tools and samples in a single report
    Philip Ewels, Mans Magnusson, Sverker Lundin and Max Kaller
    Bioinformatics (2016)
    doi: 10.1093/bioinformatics/btw354
    PMID: 27312411 
    https://github.com/ewels/MultiQC

"""
import os
import json
import pandas as pd
import re
import sqlite3

from bio_qcmetrics_tool.utils.parse import parse_type
from bio_qcmetrics_tool.modules.base import ExportQcModule


class ExportStarStats(ExportQcModule):
    """Extract STAR logs/gene counts metrics"""

    def __init__(self, options=dict()):
        super().__init__(name="star", options=options)

    @classmethod
    def __add_arguments__(cls, subparser):
        subparser.add_argument(
            "--final_log_inputs", action="append", help="Input star log file."
        )

        subparser.add_argument(
            "--gene_counts_inputs", action="append", help="Input star gene counts file."
        )

        subparser.add_argument(
            "-j",
            "--job_uuid",
            type=str,
            required=True,
            help="The job uuid associated with the inputs.",
        )

        subparser.add_argument(
            "--bam",
            action="append",
            help="The bam file associated with the inputs in the same order.",
        )

    @classmethod
    def __get_description__(cls):
        return "Extract STAR logs/gene counts metrics."

    def do_work(self):
        super().do_work()

        if (
            not self.options["final_log_inputs"]
            and not self.options["gene_counts_inputs"]
        ):
            msg = "You must provide at least one --final_log_inputs or --gene_counts_inputs parameter"
            self.logger.error(msg)
            raise Exception(msg)

        self.logger.info(
            "Processing {0} STAR log files...".format(
                len(self.options["final_log_inputs"])
            )
        )

        self.logger.info(
            "Processing {0} STAR gene count files...".format(
                len(self.options["gene_counts_inputs"])
            )
        )

        if self.options["final_log_inputs"]:
            for star_file, bam in zip(
                self.options["final_log_inputs"], self.options["bam"]
            ):
                source = os.path.basename(star_file)
                assert source not in self.data, "Duplicate input files?? {0}".format(
                    source
                )
                self.logger.info("Processing {0}".format(source))
                self.data[source] = dict()
                self.data[source]["star_stats"] = self.parse_star_final_log(star_file)
                self.data[source]["star_stats"]["bam"] = os.path.basename(bam)

        if self.options["gene_counts_inputs"]:
            for star_file, bam in zip(
                self.options["gene_counts_inputs"], self.options["bam"]
            ):
                source = os.path.basename(star_file)
                assert source not in self.data, "Duplicate input files?? {0}".format(
                    source
                )
                self.logger.info("Processing {0}".format(source))
                self.data[source] = dict()
                self.data[source][
                    "star_gene_counts"
                ] = self.parse_star_genecount_report(star_file)
                self.data[source]["star_gene_counts"]["bam"] = os.path.basename(bam)

        # Export
        self.export()

    def parse_star_final_log(self, fil):
        regexes = {
            "total_reads": r"Number of input reads \|\s+(\d+)",
            "avg_input_read_length": r"Average input read length \|\s+([\d\.]+)",
            "uniquely_mapped": r"Uniquely mapped reads number \|\s+(\d+)",
            "uniquely_mapped_percent": r"Uniquely mapped reads % \|\s+([\d\.]+)",
            "avg_mapped_read_length": r"Average mapped length \|\s+([\d\.]+)",
            "num_splices": r"Number of splices: Total \|\s+(\d+)",
            "num_annotated_splices": r"Number of splices: Annotated \(sjdb\) \|\s+(\d+)",
            "num_GTAG_splices": r"Number of splices: GT/AG \|\s+(\d+)",
            "num_GCAG_splices": r"Number of splices: GC/AG \|\s+(\d+)",
            "num_ATAC_splices": r"Number of splices: AT/AC \|\s+(\d+)",
            "num_noncanonical_splices": r"Number of splices: Non-canonical \|\s+(\d+)",
            "mismatch_rate": r"Mismatch rate per base, % \|\s+([\d\.]+)",
            "deletion_rate": r"Deletion rate per base \|\s+([\d\.]+)",
            "deletion_length": r"Deletion average length \|\s+([\d\.]+)",
            "insertion_rate": r"Insertion rate per base \|\s+([\d\.]+)",
            "insertion_length": r"Insertion average length \|\s+([\d\.]+)",
            "multimapped": r"Number of reads mapped to multiple loci \|\s+(\d+)",
            "multimapped_percent": r"% of reads mapped to multiple loci \|\s+([\d\.]+)",
            "multimapped_toomany": r"Number of reads mapped to too many loci \|\s+(\d+)",
            "multimapped_toomany_percent": r"% of reads mapped to too many loci \|\s+([\d\.]+)",
            "unmapped_mismatches_percent": r"% of reads unmapped: too many mismatches \|\s+([\d\.]+)",
            "unmapped_tooshort_percent": r"% of reads unmapped: too short \|\s+([\d\.]+)",
            "unmapped_other_percent": r"% of reads unmapped: other \|\s+([\d\.]+)",
            "chimeric": r"Number of chimeric reads \|\s+(\d+)",
            "chimeric_percent": r"% of chimeric reads \|\s+([\d\.]+)",
        }

        with open(fil, "rt") as fh:
            raw_data = fh.read()

        parsed_data = {}
        for k, r in regexes.items():
            r_search = re.search(r, raw_data, re.MULTILINE)
            if r_search:
                parsed_data[k] = float(r_search.group(1))

        try:
            total_mapped = (
                parsed_data["uniquely_mapped"]
                + parsed_data["multimapped"]
                + parsed_data["multimapped_toomany"]
            )
            unmapped_count = parsed_data["total_reads"] - total_mapped
            total_unmapped_percent = (
                parsed_data["unmapped_mismatches_percent"]
                + parsed_data["unmapped_tooshort_percent"]
                + parsed_data["unmapped_other_percent"]
            )
            try:
                parsed_data["unmapped_mismatches"] = int(
                    round(
                        unmapped_count
                        * (
                            parsed_data["unmapped_mismatches_percent"]
                            / total_unmapped_percent
                        ),
                        0,
                    )
                )
                parsed_data["unmapped_tooshort"] = int(
                    round(
                        unmapped_count
                        * (
                            parsed_data["unmapped_tooshort_percent"]
                            / total_unmapped_percent
                        ),
                        0,
                    )
                )
                parsed_data["unmapped_other"] = int(
                    round(
                        unmapped_count
                        * (
                            parsed_data["unmapped_other_percent"]
                            / total_unmapped_percent
                        ),
                        0,
                    )
                )
            except ZeroDivisionError:
                parsed_data["unmapped_mismatches"] = 0
                parsed_data["unmapped_tooshort"] = 0
                parsed_data["unmapped_other"] = 0
        except KeyError:
            pass

        if len(parsed_data) == 0:
            return None
        return parsed_data

    def parse_star_genecount_report(self, f):
        """ Parse a STAR gene counts output file """
        # Three numeric columns: unstranded, stranded/first-strand, stranded/second-strand
        keys = ["N_unmapped", "N_multimapping", "N_noFeature", "N_ambiguous"]
        unstranded = {"N_genes": 0}
        first_strand = {"N_genes": 0}
        second_strand = {"N_genes": 0}
        num_errors = 0
        num_genes = 0
        with open(f, "rt") as fh:
            for l in fh:
                s = l.split("\t")
                try:
                    for i in [1, 2, 3]:
                        s[i] = int(s[i])
                    if s[0] in keys:
                        unstranded[s[0]] = s[1]
                        first_strand[s[0]] = s[2]
                        second_strand[s[0]] = s[3]
                    else:
                        unstranded["N_genes"] += s[1]
                        first_strand["N_genes"] += s[2]
                        second_strand["N_genes"] += s[3]
                        num_genes += 1
                except IndexError:
                    # Tolerate a few errors in case there is something random added at the top of the file
                    num_errors += 1
                    if num_errors > 10 and num_genes == 0:
                        self.logger.warning("Error parsing {}".format(f["fn"]))
                        return None
        if num_genes > 0:
            return {
                "unstranded": unstranded,
                "first_strand": first_strand,
                "second_strand": second_strand,
            }
        else:
            return None

    def to_sqlite(self):
        star_stats = []
        star_genes = []
        for source in sorted(self.data):
            if "star_stats" in self.data[source]:
                bam = self.data[source]["star_stats"]["bam"]
                for key in sorted(self.data[source]["star_stats"]):
                    if key == "bam":
                        continue
                    row = {
                        "category": key,
                        "value": self.data[source]["star_stats"][key],
                        "star_file": source,
                        "bam": bam,
                        "job_uuid": self.options["job_uuid"],
                    }
                    star_stats.append(row)

            if "star_gene_counts" in self.data[source]:
                bam = self.data[source]["star_gene_counts"]["bam"]
                for strand in self.data[source]["star_gene_counts"]:
                    if strand == "bam":
                        continue
                    for key in sorted(self.data[source]["star_gene_counts"][strand]):
                        row = dict()
                        row["category"] = key
                        row["value"] = self.data[source]["star_gene_counts"][strand][
                            key
                        ]
                        row["strand"] = strand
                        row["star_file"] = source
                        row["bam"] = bam
                        row["job_uuid"] = self.options["job_uuid"]
                        star_genes.append(row)

        self.logger.info(
            "Writing metrics to sqlite file {0}".format(self.options["output"])
        )

        with sqlite3.connect(self.options["output"]) as conn:

            if star_stats:
                df = pd.DataFrame(star_stats)
                table_name = "star_stats"
                df.to_sql(table_name, conn, if_exists="append")

            if star_genes:
                df = pd.DataFrame(star_genes)
                table_name = "star_gene_counts"
                df.to_sql(table_name, conn, if_exists="append")
