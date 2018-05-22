from __future__ import absolute_import

from .base import PicardMetric

class QualityDistributionMetrics(PicardMetric):
    picard_tool_name = "CollectQualityDistributionMetrics"

    def __init__(self, source, histogram, field_names=[], values=[]):
        super().__init__(
            class_name="QualityDistributionMetrics",
            source=source,
            field_names=field_names,
            values=values,
            derived_from_key='bam',
            histogram=histogram
        )

    @classmethod
    def from_picard_file_instance(cls, obj):
        return cls(obj.fpath, obj._histograms[0])

    def extract_metrics(self):
        super().extract_metrics()
        dat = {
            'derived_from_key': self.derived_from_key,
            'metric': None,
            'histogram': {
                'colnames': self.histogram['labels'],
                'data': self.histogram['values']
            }
        }
        return dat

    @staticmethod
    def codec_match(obj):
        if not obj._metrics and obj._histograms:
            if obj._histograms[0]['bin'] == 'QUALITY' and obj._histograms[0]['labels'][1] == 'COUNT_OF_Q':
                return True
        return False

    def for_sqlite(self, job_uuid, source):
        pass