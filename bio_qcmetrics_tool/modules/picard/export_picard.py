"""QC Module for Exporting Picard Metrics"""
import os
import json
import pandas as pd
import sqlite3

from bio_qcmetrics_tool.utils.parse import parse_type
from bio_qcmetrics_tool.modules.base import ExportQcModule
from bio_qcmetrics_tool.modules.picard.codec import PicardMetricsFile

class ExportPicardMetrics(ExportQcModule):
    """Extract Picard metrics"""
    def __init__(self, options=dict()):
        super().__init__(name="picard", options=options)

    @classmethod
    def __add_arguments__(cls, subparser):
        subparser.add_argument('-i', '--inputs', action='append', required=True,
            help='Input picard metrics file. May be used one or more times')

        subparser.add_argument('-j', '--job_uuid', type=str, required=True,
            help='The job uuid associated with the inputs.')

        subparser.add_argument('--derived_from_file', type=str,
            help='The file that the metrics were drived from (e.g., bam file).')

    @classmethod
    def __get_description__(cls):
        return "Extract Picard metrics."

    def do_work(self):
        super().do_work()

        self.logger.info('Processing {0} Picard metrics files...'.format(
            len(self.options['inputs'])))

        for picard_file in self.options['inputs']:
            source = os.path.basename(picard_file)
            assert source not in self.data, "Duplicate input files?? {0}".format(source)
            self.data[source] = {}
            self.logger.info("Processing {0}".format(source))
            picard_metrics_obj = PicardMetricsFile(picard_file)
            self.picard[source][picard_metrics_obj.metrics.class_name] = \
                picard_metrics_obj.metrics.extract_metrics()

        self.extract()

    def to_sqlite(self):
        data = {}
        derived_from = os.path.basename(self.options['derived_from_file']) \
            if self.options['derived_from_file'] else None
        for source in sorted(self.data):
            for section in self.data[source]:
                derived_key = self.data[source][section]['derived_from_key']
                if self.data[source][section]['metric']:
                    table = 'picard_{0}'.format(section)
                    if table not in data:
                        data[table] = []
                    record = self.data[source][section]['metric']
                    for row in record['data']:
                        curr = dict(zip(record['colnames'], row))
                        curr['job_uuid'] = self.options['job_uuid']
                        curr['picard_metrics'] = source
                        curr[derived_key] = derived_from
                        data[table].append(curr)

                if self.data[source][section]['histogram']:
                    table = 'picard_{0}_histogram'.format(section)
                    if table not in data:
                        data[table] = []
                    record = self.data[source][section]['histogram']
                    hist_bin = record['colnames'][0]
                    hist_cols = record['colnames'][1:]
                    for col in hist_cols:
                        for row in record['data']:
                            rec = dict(zip(record['colnames'], row))
                            curr = dict()
                            curr['job_uuid'] = self.options['job_uuid']
                            curr['picard_metrics'] = source
                            curr[derived_key] = derived_from
                            curr[hist_bin] = rec[hist_bin]
                            curr['colname'] = col
                            curr['value'] = rec[col]
                            data[table].append(curr)

        self.logger.info("Writing metrics to sqlite file {0}".format(
            self.options['outpute']))

        with sqlite3.connect(self.options['output']) as conn:
            for table in data:
                if data[table]:
                    df = pd.DataFrame(data[table])
                    df.to_sql(table, conn, if_exists='append')
