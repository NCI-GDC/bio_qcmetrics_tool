"""Module containing exceptions raised by QC tools"""


class BioQcMetricsException(Exception):
    """Base for all custom exceptions"""

    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return self.message


class ParserException(BioQcMetricsException):
    """Exception thrown when a QC tool can't parse a file"""

    pass


class UnsupportedTypeException(BioQcMetricsException):
    """Exception thrown when tool encounters an unsupported type"""

    pass


class ClassNotFoundException(BioQcMetricsException):
    """Exception thrown when tool is unable to locate a class"""

    pass


class DuplicateInputException(BioQcMetricsException):
    """Exception thrown when a QC tool encounters duplicate inputs"""

    pass
