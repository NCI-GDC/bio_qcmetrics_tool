"""QC Module for Picard Metrics"""
import importlib
import inspect
import pkgutil
import sys
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, List, Optional, Type, TypedDict, Union

from bio_qcmetrics_tool.utils.logger import Logger

if TYPE_CHECKING:
    from bio_qcmetrics_tool.modules.picard.codec import PicardMetricsFile


class HistogramDict(TypedDict):
    colnames: Any
    data: Any


class MetricsDict(TypedDict):
    colnames: Any
    data: Any


class ExtractedMetricsDict(TypedDict):
    derived_from_key: Optional[str]
    metric: Optional[MetricsDict]
    histogram: Optional[HistogramDict]


class PicardMetric(metaclass=ABCMeta):
    """
    Base class for all Picard metrics objects. These objects act as a
    container for the metrics/histograms encountered, the serializer of the
    metrics, and implement the function to check whether a PicardMetricsFile
    object matches a particular metric.
    """

    def __init__(
        self,
        class_name: str,
        source: str,
        histogram: Optional[dict] = None,
        derived_from_key: Optional[str] = None,
        field_names: Optional[List[str]] = None,
        values: Optional[List[str]] = None,
    ):
        """
        Initialze a PicardMetric object.

        :param class_name: custom name of the metrics class
        :type class_name: str

        :param source: the path to the source picard metrics file
        :type source: str

        :param histogram: extracted histogram data if any
        :type histogram: dict

        :param derived_from_key: the column name for the derived from file (e.g., bam)
        :type derived_from_key: str
        """
        self.logger = Logger.get_logger(self.__class__.__name__)
        self.class_name: str = class_name
        self.source: str = source
        self.field_names: List[str] = [] if field_names is None else field_names
        self.values: list = [] if values is None else values
        self.histogram: Optional[dict] = histogram
        self.derived_from_key: Optional[str] = derived_from_key

    @classmethod
    @abstractmethod
    def from_picard_file_instance(cls, obj: 'PicardMetricsFile') -> 'PicardMetric':
        """
        Initialize the class from the PicardMetricsFile instance.
        """

    def extract_metrics(self) -> ExtractedMetricsDict:
        """
        Entry point to get formatted metrics results.
        """
        self.logger.info("{0} - {1}".format(self.__class__.__name__, self.source))
        metrics_dict: Optional[MetricsDict] = None
        histogram_dict: Optional[HistogramDict] = None
        if self.field_names and self.values:
            metrics_dict = MetricsDict(colnames=self.field_names, data=self.values)
        if self.histogram is not None:
            histogram_dict = HistogramDict(
                colnames=self.histogram["labels"], data=self.histogram["values"]
            )

        dat = ExtractedMetricsDict(
            derived_from_key=self.derived_from_key,
            metric=metrics_dict,
            histogram=histogram_dict,
        )
        return dat

    def add_field_names(self, fields: Union[list, str]) -> None:
        if isinstance(fields, list):
            self.field_names.extend(fields)
        else:
            self.field_names.append(fields)

    def add_value_row(self, row: list) -> None:
        assert isinstance(row, list)
        self.values.append(row)

    @staticmethod
    @abstractmethod
    def codec_match(obj: 'PicardMetricsFile') -> bool:
        """
        All subclasses must implement this function to check whether the
        metrics file object matches this class.
        """
        raise NotImplementedError("Not implemented!")


PICARD_METRICS_OBJECTS: List[Type[PicardMetric]] = []

if not PICARD_METRICS_OBJECTS:

    def predicate(obj: PicardMetric) -> bool:
        return inspect.isclass(obj) and issubclass(obj, PicardMetric)

    mod = sys.modules["bio_qcmetrics_tool.modules.picard.metrics"]
    for p in pkgutil.iter_modules(mod.__path__, mod.__name__ + "."):
        if p[1] != "bio_qcmetrics_tool.modules.picard.metrics.base":
            try:
                curr = sys.modules[p[1]]
            except KeyError:
                curr = importlib.import_module(p[1])

            for m in inspect.getmembers(curr, predicate):
                if m[0] != "PicardMetric":
                    PICARD_METRICS_OBJECTS.append(m[1])
