from __future__ import absolute_import

from .base import PicardMetric

class QualityByCycleMetrics(PicardMetric):
    picard_tool_name = "CollectQualityByCycleMetrics"

    def __init__(self, source, histogram, field_names=[], values=[]):
        super().__init__(
            class_name="QualityByCycleMetrics",
            source=source,
            field_names=field_names,
            values=values,
            derived_from_key='bam',
            histogram=histrogram
        )

    @classmethod
    def from_picard_file_instance(cls, obj):
        return cls(obj.fpath, obj._histograms[0])

    @staticmethod
    def codec_match(obj):
        if not obj._metrics and obj._histograms:
            if obj._histograms[0]['bin'] == 'CYCLE' and obj._histograms[0]['labels'][1] == 'MEAN_QUALITY':
                return True
        return False

    def for_sqlite(self, job_uuid, source):
        pass
