from __future__ import absolute_import

from typing import Optional

from bio_qcmetrics_tool.modules.picard.codec import PicardMetricsFile

from .base import PicardMetric


class QualityByCycleMetrics(PicardMetric):
    picard_tool_name = "CollectQualityByCycleMetrics"

    def __init__(
        self,
        source: str,
        histogram: dict,
        field_names: Optional[list] = None,
        values: Optional[list] = None,
    ):
        super().__init__(
            class_name="QualityByCycleMetrics",
            source=source,
            field_names=field_names,
            values=values,
            derived_from_key="bam",
            histogram=histogram,
        )

    @classmethod
    def from_picard_file_instance(
        cls, obj: PicardMetricsFile
    ) -> 'QualityByCycleMetrics':
        return cls(obj.fpath, obj._histograms[0])

    @staticmethod
    def codec_match(obj: PicardMetricsFile) -> bool:
        if not obj._metrics and obj._histograms:
            if (
                obj._histograms[0]["bin"] == "CYCLE"
                and obj._histograms[0]["labels"][1] == "MEAN_QUALITY"
            ):
                return True
        return False
