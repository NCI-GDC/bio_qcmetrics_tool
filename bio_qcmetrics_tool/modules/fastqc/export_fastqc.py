"""Extract metrics from raw FastQC zip archives and import into
the sqlite db.

Some of the file-parsing logic is adapted from:

    MultiQC: Summarize analysis results for multiple tools and samples in a single report
    Philip Ewels, Mans Magnusson, Sverker Lundin and Max Kaller
    Bioinformatics (2016)
    doi: 10.1093/bioinformatics/btw354
    PMID: 27312411 
    https://github.com/ewels/MultiQC

"""
import os
import zipfile
import pandas as pd
import sqlite3

from bio_qcmetrics_tool.utils.parse import parse_type
from bio_qcmetrics_tool.modules.base import ExportQcModule 

class ExportFastqc(ExportQcModule):
    """Export FastQC metrics"""
    def __init__(self, options=dict()):
        super().__init__(name="fastqc", options=options)

    @classmethod
    def __add_arguments__(cls, subparser):
        subparser.add_argument('-i', '--inputs', action='append', required=True,
            help='Input fastqc zip file. May be used one or more times')

        subparser.add_argument('-j', '--job_uuid', type=str, required=True,
            help='The job uuid associated with the inputs.')

    @classmethod
    def __get_description__(cls):
        return "Extract FastQC report from zip archive(s)."

    def do_work(self):
        super().do_work()

        self.logger.info('Processing {0} FastQC zip files...'.format(
            len(self.options['inputs'])))

        for fqzipfile in self.options['inputs']:
            basename = os.path.basename(fqzipfile)
            assert basename not in self.data, "Duplicate input files?? {0}".format(basename)
            self.logger.info("Processing {0}".format(basename))
            self.data[basename] = dict()

            with zipfile.ZipFile(fqzipfile, mode='r') as fqzip:
                # Get file names
                fqc_data_file, fqc_summary_file = self.get_fastqc_file_names(fqzip)

                # Get fastq name
                with fqzip.open(fqc_data_file, mode='r') as dfo:
                    fastq_name = self.get_fastq_name(dfo)

                if not fastq_name:
                    msg = "Unable to find fastq name in {0}".format(fqzipfile)
                    self.logger.error(msg)
                    raise Exception(msg)

                # Load fastqc summary
                with fqzip.open(fqc_summary_file, mode='r') as sfo:
                    self.parse_fastqc_summary(basename, fastq_name, sfo)

                # Load fastqc data
                with fqzip.open(fqc_data_file, mode='r') as dfo:
                    self.parse_fastqc_data(basename, fastq_name, dfo)

        # Export
        self.export()

    def to_sqlite(self):
        """
        Export to sqlite file.
        """
        sum_dat = []
        detail_dat = {}
        for source in sorted(self.data):
            for section in self.data[source]:
                if section == 'fastqc_summary':
                    curr = self.data[source][section]
                    curr['fastqc_zip'] = source
                    sum_dat.append(curr)
                else:
                    if section not in detail_dat:
                        detail_dat[section] = []

                    record = self.data[source][section]
                    curr = record['data']
                    if section.lower() == 'basic_statistics':
                        for k in curr:
                            rec = {}
                            rec['job_uuid'] = record['job_uuid']
                            rec['fastq'] = record['fastq']
                            rec['fastqc_zip'] = source
                            val = str(curr[k]) if curr[k] is not None else None
                            rec['Measure'] = k
                            rec['Value'] = val
                            detail_dat[section].append(rec)
                    elif record.get('colnames'):
                        for row in curr:
                            rec = dict(zip(
                                record['colnames'],
                                [str(i) if i is not None else None for i in row]))
                            rec['job_uuid'] = record['job_uuid'] 
                            rec['fastq'] = record['fastq']
                            rec['fastqc_zip'] = source
                            detail_dat[section].append(rec)

        self.logger.info("Writing metrics to sqlite file {0}".format(
            self.options['output']))

        with sqlite3.connect(self.options['output']) as conn:
            # Summary table
            sum_df = pd.DataFrame(sum_dat)
            table_name = 'fastqc_summary'
            sum_df.to_sql(table_name, conn, if_exists='append')

            # All other tables
            for k in detail_dat:
                if detail_dat[k]:
                    table_name = 'fastqc_data_{0}'.format(k)
                    df = pd.DataFrame(detail_dat[k])
                    df.to_sql(table_name, conn, if_exists='append')

    def get_fastqc_file_names(self, zip_object):
        """
        Extract the fastqc file names from the fastqc zip.
        """
        fastqc_data_file = None
        fastqc_summary_file = None
        for fname in zip_object.namelist():
            if os.path.basename(fname) == 'fastqc_data.txt':
                fastqc_data_file = fname
            elif os.path.basename(fname) == 'summary.txt':
                fastqc_summary_file = fname
        assert fastqc_data_file is not None, 'Unable to find data file!!'
        assert fastqc_summary_file is not None, 'Unable to find summary file!!'

        return fastqc_data_file, fastqc_summary_file

    def get_fastq_name(self, fo):
        """Extracts fastq name from fastqc data file"""
        for line in fo:
            line = line.decode('utf-8').rstrip('\r\n')
            if line.startswith('Filename\t'):
                cols = line.split('\t')
                return cols[1].strip()

    def parse_fastqc_summary(self, source, fastq, fo):
        """
        Extracts the summary data from the fastqc_summary file.
        """
        section = 'fastqc_summary'
        self.data[source][section] = {'fastq': fastq, 'job_uuid': self.options['job_uuid']}
        for line in fo:
            state, category, fname = line.decode('utf-8').rstrip('\r\n').split('\t')
            self.data[source][section][category] = state
        if 'Per tile sequence quality' not in self.data[source][section]:
            self.data[source][section]['Per tile sequence quality'] = None

    def parse_fastqc_data(self, source, fastq, fo):
        """
        Extracts all the sections from the fastqc data file.
        """
        total_dedup = None
        for section, state, header, extra, data in self._fastqc_data_section_generator(fo):
            if section not in self.data[source]:
                self.data[source][section] = {
                    'fastq': fastq,
                    'job_uuid': self.options['job_uuid'],
                    'data': None}

            if not header or not data:
                self.data[source][section]['data'] = data

            elif section.lower() == 'basic_statistics':
                self.data[source][section]['data'] = {}
                for row in data:
                    curr = dict(zip(header, row))
                    if curr['Measure'] == 'Filename':
                        continue
                    else:
                        self.data[source][section]['data'][curr['Measure']] = \
                            parse_type(curr['Value'])

            else:
                self.data[source][section]['data'] = []
                self.data[source][section]['colnames'] = header

                if extra and section.lower() == 'sequence_duplication_levels':
                    total_dedup = parse_type(extra)
                for record in data:
                    row = [parse_type(i) for i in record]
                    self.data[source][section]['data'].append(row)

        self.data[source]\
            ['Basic_Statistics']\
            ['data']\
            ['Total Deduplicated Percentage'] = total_dedup

    def _fastqc_data_section_generator(self, fo):
        """
        Extract a section of fastqc data and yield it.
        """
        section = None
        state = None
        header = None
        extra = None
        data = []
        for line in fo:
            line = line.decode('utf-8').rstrip('\r\n')
            if line.startswith('##') and not section:
                continue
            elif line.startswith('>>END_MODULE'):
                yield section, state, header, extra, data
                section = None
                header = None
                extra = None
                data = []
            elif line.startswith('>>'):
                sdat = line[2:].split('\t')
                section = sdat[0].replace(' ', '_')
                state = sdat[1]
            elif line.startswith('#') and section:
                if line.startswith('#Total Deduplicated Percentage'):
                    extra = line.split('\t')[1]
                else:
                    header = line[1:].split('\t')
            else:
                data.append(line.split('\t'))
        if section:
            yield section, state, header, extra, data
