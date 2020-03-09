"""Codec for Picard metrics files."""
import os

from bio_qcmetrics_tool.modules.picard.metrics.base import PICARD_METRICS_OBJECTS
from bio_qcmetrics_tool.modules.exceptions import ParserException
from bio_qcmetrics_tool.utils.parse import parse_type


class PicardMetricsFile:
    """Represents a single file output by a Picard metrics tool"""

    MAJOR_HEADER_PREFIX = "## "
    MINOR_HEADER_PREFIX = "# "
    SEPARATOR = "\t"
    HISTO_HEADER = "## HISTOGRAM\t"
    METRIC_HEADER = "## METRICS CLASS\t"

    def __init__(self, fpath, tool=None, headers=[], metrics=None):
        """
        Initialize with the path to Picard metrics file. The slots of this
        class include:

        :param fpath: Picard metrics file path
        :type fpath: str

        :param tool: Picard tool name parsed from header
        :type fpath: str

        :param headers: list of header string 
        :type headers: list

        :param metrics: subclass of PicardMetric
        :type metrics: `~bio_qcmetrics_tool.modules.picard.metrics.base.PicardMetric`
        """
        self.fpath = fpath
        self.tool = tool

        self.headers = []
        self.metrics = metrics

        # Private list of dicts containing parsed metrics lines.
        # The dictionaries contain "class", "fields", and "values"
        self._metrics = []
        # Private list of dicts containing parsed histogram lines
        # The dictionaries contain "class", "bin", "labels", and "values"
        self._histograms = []

        self.parse_file()

    def parse_file(self):
        """
        Main wrapper function for parsing the provided Picard file.
        """
        if not self.headers:
            self._parser()
            # Now we need to determine the proper class to load
            metrics_class = self.load_class()
            self.metrics = metrics_class.from_picard_file_instance(self)

    def _parser(self):
        """
        Parses generic picard Metrics file.
        """
        header = None
        cls = None
        with open(self.fpath, "rt") as fh:
            line = ""
            for line in fh:
                # Parse headers
                line = line.rstrip("\r\n")
                if line == "":
                    continue
                elif line.startswith(self.METRIC_HEADER) or line.startswith(
                    self.HISTO_HEADER
                ):
                    break
                elif line.startswith(self.MAJOR_HEADER_PREFIX):
                    if header:
                        raise ParserException(
                            "Consecutive header class lines encountered."
                        )
                    cls = line[len(self.MAJOR_HEADER_PREFIX) :].strip()
                elif line.startswith(self.MINOR_HEADER_PREFIX):
                    if not cls:
                        raise ParserException(
                            "Header class must precede header value: {0}".format(line)
                        )

                    val = line[len(self.MINOR_HEADER_PREFIX) :]
                    header = (cls, val)
                    if not self.headers:
                        self.tool = val.split(" ")[0]
                    self.headers.append(header)
                    header = None
                else:
                    raise ParserException(
                        "Illegal state. Found following string in metrics file header: {0}".format(
                            line
                        )
                    )

            # Read space between headers and metrics
            while True and not line.strip().startswith(self.MAJOR_HEADER_PREFIX):
                line = fh.readline().rstrip("\r\n")

            if line:
                line = line.rstrip("\r\n").lstrip()

                # Read metrics if present
                if line.startswith(self.METRIC_HEADER):
                    # Get metrics class
                    mcls = line.split(self.SEPARATOR)[1]

                    field_names = fh.readline().rstrip("\r\n").split(self.SEPARATOR)

                    metric = {"class": mcls, "fields": field_names, "values": []}

                    # Load all the values
                    while True:
                        line = fh.readline().rstrip("\r\n")
                        if not line:
                            break
                        else:
                            cols = [parse_type(i) for i in line.split(self.SEPARATOR)]
                            metric["values"].append(cols)
                    self._metrics.append(metric)

            # Skip blank lines between metrics and histograms
            while True and not line.strip().startswith(self.MAJOR_HEADER_PREFIX):
                line = fh.readline().rstrip("\r\n")

            # Read the histograms if any are present
            if line:
                line = line.rstrip("\r\n").lstrip()
                if line.startswith(self.HISTO_HEADER):
                    key_cls = line.split(self.SEPARATOR)[1].strip()
                    labels = fh.readline().rstrip("\r\n").split(self.SEPARATOR)
                    hist = dict()
                    hist["class"] = key_cls
                    hist["bin"] = labels[0]
                    hist["labels"] = labels
                    hist["values"] = []
                    while True:
                        line = fh.readline().rstrip("\r\n")
                        if not line:
                            break
                        else:
                            cols = [parse_type(i) for i in line.split(self.SEPARATOR)]
                            hist["values"].append(cols)
                    self._histograms.append(hist)

    def load_class(self):
        """
        Loads the approppriate PicardMetrics class.
        """
        for cls in PICARD_METRICS_OBJECTS:
            if cls.codec_match(self):
                return cls
        raise ClassNotFoundException(
            "Could not load picard metrics class for metrics file: {0}".format(
                self.fpath
            )
        )
