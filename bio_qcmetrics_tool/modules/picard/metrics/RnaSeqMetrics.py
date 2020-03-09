from __future__ import absolute_import

from .base import PicardMetric


class RnaSeqMetrics(PicardMetric):
    picard_tool_name = "CollectRnaSeqMetrics"

    def __init__(self, source, histogram, field_names=[], values=[]):
        super().__init__(
            class_name="RnaSeqMetrics",
            derived_from_key="bam",
            source=source,
            field_names=field_names,
            values=values,
            histogram=histogram,
        )

    @classmethod
    def from_picard_file_instance(cls, obj):
        return cls(
            obj.fpath,
            obj._histograms[0],
            obj._metrics[0]["fields"],
            obj._metrics[0]["values"],
        )

    @staticmethod
    def codec_match(obj):
        if obj._metrics and "rnaseqmetrics" in obj._metrics[0]["class"].lower():
            return True
        else:
            return False

    def for_sqlite(self, job_uuid, source):
        pass
