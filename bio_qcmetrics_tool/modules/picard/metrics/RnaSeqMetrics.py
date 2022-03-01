from __future__ import absolute_import

from typing import Optional

from bio_qcmetrics_tool.modules.picard.codec import PicardMetricsFile

from .base import PicardMetric


class RnaSeqMetrics(PicardMetric):
    picard_tool_name = "CollectRnaSeqMetrics"

    def __init__(
        self,
        source: str,
        histogram: dict,
        field_names: Optional[list] = None,
        values: Optional[list] = None,
    ):
        super().__init__(
            class_name="RnaSeqMetrics",
            derived_from_key="bam",
            source=source,
            field_names=field_names,
            values=values,
            histogram=histogram,
        )

    @classmethod
    def from_picard_file_instance(cls, obj: PicardMetricsFile) -> 'RnaSeqMetrics':
        return cls(
            obj.fpath,
            obj._histograms[0],
            obj._metrics[0]["fields"],
            obj._metrics[0]["values"],
        )

    @staticmethod
    def codec_match(obj: PicardMetricsFile) -> bool:
        if obj._metrics and "rnaseqmetrics" in obj._metrics[0]["class_name"].lower():
            return True
        else:
            return False
