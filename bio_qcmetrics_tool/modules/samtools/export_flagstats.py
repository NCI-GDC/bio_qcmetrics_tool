"""QC Module for Exporting samtools flagstats"""
import json
import os
import re
import pandas as pd
import sqlite3

from bio_qcmetrics_tool.utils.parse import parse_type, get_read_func
from bio_qcmetrics_tool.modules.base import ExportQcModule
from bio_qcmetrics_tool.modules.exceptions import DuplicateInputException, ParserException

class ExportSamtoolsFlagstats(ExportQcModule):
    """Extract samtools flagstats""" 
    def __init__(self, options=dict()):
        super().__init__(name="samtools flagstats", options=options)

    @classmethod
    def __add_arguments__(cls, subparser):
        subparser.add_argument('-i', '--inputs', action='append', required=True,
            help='Input flagstats file. May be used one or more times')

        subparser.add_argument('-j', '--job_uuid', type=str, required=True,
            help='The job uuid associated with the inputs.')

        subparser.add_argument('-b', '--bam', type=str, required=True,
            help='The bam that the metrics were derived from.')

    @classmethod
    def __get_description__(cls):
        return "Extract samtools flagstats metrics." 

    def do_work(self):
        super().do_work()

        self.logger.info('Processing {0} flagstat files...'.format(
            len(self.options['inputs'])))

        for flagfile in self.options['inputs']:
            basename = os.path.basename(flagfile)
            if basename in self.data:
                raise DuplicateInputException("Duplicate input files?? {0}".format(basename))
            self.logger.info("Processing {0}".format(basename))
            self.data[basename] = dict()
            rfunc = get_read_func(flagfile) 
            fsize = os.stat(flagfile).st_size
            if fsize > 5000:
                raise ParserException("Input file size '{0}' is larger than expected! Are you sure this is a flagstats file?".format(fsize))

            with rfunc(flagfile, 'rt') as fh:
                fdat = fh.read()
                self.data[basename]['flagstat'] = {
                    'bam': os.path.basename(self.options['bam']),
                    'job_uuid': self.options['job_uuid'],
                    'data': self._parse_flagstat(fdat)
                }

        # Export data
        self.export()

    def to_sqlite(self):
        data = [] 
        for source in sorted(self.data):
            record = self.data[source]['flagstat']
            for section in sorted(record['data']): 
                curr = {
                    'job_uuid': record['job_uuid'],
                    'bam': record['bam'],
                    'flagstat_file': source,
                    'category': section,
                    'n_passed': record['data'][section].get('passed'),
                    'n_failed': record['data'][section].get('failed')
                } 
                data.append(curr)

        if data:
            self.logger.info("Writing metrics to sqlite file {0}".format(
                self.options['output']))

            with sqlite3.connect(self.options['output']) as conn:
                df = pd.DataFrame(data)
                table_name = 'samtools_flagstat'
                df.to_sql(table_name, conn, if_exists='append')

    def _parse_flagstat(self, fh):
        """
        Parse the flagstat data from the loaded file data 
        """
        parsed_data = {}
        flagstat_regexes = {
            'total': r"(\d+) \+ (\d+) in total \(QC-passed reads \+ QC-failed reads\)",
            'secondary': r"(\d+) \+ (\d+) secondary",
            'supplementary': r"(\d+) \+ (\d+) supplementary",
            'duplicates': r"(\d+) \+ (\d+) duplicates",
            'mapped': r"(\d+) \+ (\d+) mapped \((.+):(.+)\)",
            'paired in sequencing': r"(\d+) \+ (\d+) paired in sequencing",
            'read1': r"(\d+) \+ (\d+) read1",
            'read2': r"(\d+) \+ (\d+) read2",
            'properly paired': r"(\d+) \+ (\d+) properly paired \((.+):(.+)\)",
            'with itself and mate mapped': r"(\d+) \+ (\d+) with itself and mate mapped",
            'singletons': r"(\d+) \+ (\d+) singletons \((.+):(.+)\)",
            'with mate mapped to a different chr': r"(\d+) \+ (\d+) with mate mapped to a different chr",
            'with mate mapped to a different chr (mapQ >= 5)': r"(\d+) \+ (\d+) with mate mapped to a different chr \(mapQ>=5\)",
        }

        re_groups = ['passed', 'failed', 'passed_pct', 'failed_pct']
        for key, reg in flagstat_regexes.items():
            res = re.search(reg, fh, re.MULTILINE)
            if res:
                if key not in parsed_data: parsed_data[key] = dict()
                for i,j in enumerate(re_groups):
                    try:
                        val = res.group(i+1).strip('% ')
                        val = float(val) if ('.' in val) else int(val)
                        parsed_data[key][j] = val
                    except IndexError:
                        pass # Not all regexes have percentages
                    except ValueError:
                        parsed_data[key][j] = float('nan')

        # Calculate total read count
        try:
            parsed_data['flagstat_total'] = parsed_data['total_passed'] + parsed_data['total_failed']
        except KeyError:
            pass
        return parsed_data
