"""Codec for Picard metrics files."""
import os

from bio_qcmetrics_tool.modules.picard.metrics.base import PICARD_METRICS_OBJECTS 
from bio_qcmetrics_tool.utils.parse import parse_type 

class PicardMetricsFile:
    MAJOR_HEADER_PREFIX = "## "
    MINOR_HEADER_PREFIX = "# "
    SEPARATOR = "\t"
    HISTO_HEADER = "## HISTOGRAM\t"
    METRIC_HEADER = "## METRICS CLASS\t"

    def __init__(self, fpath):
        self.fpath = fpath
        self.tool = None 
        self.headers = []
        self.metrics = None

        self._metrics = [] 
        self._histograms = []

        self.parse_file()

    def parse_file(self):
        if not self.headers:
            self._parser()
            # Now we need to determine the proper class to load
            metrics_class = self.load_class()
            self.metrics = metrics_class.from_picard_file_instance(self) 

    def _parser(self):
        with open(self.fpath, 'rt') as fh:
            line = ""
            for line in fh:
                line = line.rstrip('\r\n')
                if line == "":
                    continue
                elif line.startswith(self.METRIC_HEADER) or \
                     line.startswith(self.HISTO_HEADER):
                    break
                elif line.startswith(self.MAJOR_HEADER_PREFIX):
                    cls = line[len(self.MAJOR_HEADER_PREFIX):].strip()
                elif line.startswith(self.MINOR_HEADER_PREFIX):
                    val = line[len(self.MINOR_HEADER_PREFIX):]
                    if not self.headers:
                        self.tool = val.split(' ')[0] 
                    self.headers.append((cls, val))

            while True and not line.strip().startswith(self.MAJOR_HEADER_PREFIX):
                line = fh.readline() 

            if line: 
                line = line.rstrip('\r\n').lstrip()
                if line.startswith(self.METRIC_HEADER):
                    mcls = line.split(self.SEPARATOR)[1]
                     
                    field_names = fh.readline().rstrip('\r\n').split(self.SEPARATOR) 

                    metric = {
                        'class': mcls,
                        'fields': field_names,
                        'values': [] 
                    }

                    while True:
                        line = fh.readline().rstrip("\r\n") 
                        if not line:
                            break
                        else:
                            cols = [parse_type(i) for i in line.split(self.SEPARATOR)]
                            metric['values'].append(cols)
                    self._metrics.append(metric)

            while True and not line.strip().startswith(self.MAJOR_HEADER_PREFIX):
                line = fh.readline() 

            if line: 
                line = line.rstrip('\r\n').lstrip()
                if line.startswith(self.HISTO_HEADER):
                    key_cls = line.split(self.SEPARATOR)[1].strip()
                    labels = fh.readline().rstrip('\r\n').split(self.SEPARATOR)
                    hist = dict()
                    hist['class'] = key_cls
                    hist['bin'] = labels[0]
                    hist['labels'] = labels
                    hist['values'] = []
                    while True:
                        line = fh.readline().rstrip("\r\n") 
                        if not line:
                            break
                        else:
                            cols = [parse_type(i) for i in line.split(self.SEPARATOR)]
                            hist['values'].append(cols) 
                    self._histograms.append(hist)

    def load_class(self):
        for cls in PICARD_METRICS_OBJECTS:
            if cls.codec_match(self):
                return cls
        raise Exception("Unable to find a compatible class for {0}".format(self.fpath)) 
