from __future__ import absolute_import

from typing import Optional

from bio_qcmetrics_tool.modules.picard.codec import PicardMetricsFile

from .base import PicardMetric


class QualityDistributionMetrics(PicardMetric):
    picard_tool_name = "CollectQualityDistributionMetrics"

    def __init__(
        self,
        source: str,
        histogram: dict,
        field_names: Optional[list] = None,
        values: Optional[list] = None,
    ):
        super().__init__(
            class_name="QualityDistributionMetrics",
            source=source,
            field_names=field_names,
            values=values,
            derived_from_key="bam",
            histogram=histogram,
        )

    @classmethod
    def from_picard_file_instance(
        cls, obj: PicardMetricsFile
    ) -> 'QualityDistributionMetrics':
        return cls(obj.fpath, obj._histograms[0])

    @staticmethod
    def codec_match(obj: PicardMetricsFile) -> bool:
        if not obj._metrics and obj._histograms:
            if (
                obj._histograms[0]["bin"] == "QUALITY"
                and obj._histograms[0]["labels"][1] == "COUNT_OF_Q"
            ):
                return True
        return False
