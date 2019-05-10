"""Module containing exceptions raised by QC tools"""

class BioQcMetricsException(Exception):
    """Base for all custom exceptions"""
    pass

class ParserException(BioQcMetricsException):
    """Exception thrown when a QC tool can't parse a file"""
    def __init__(self, message):
        self.message = message 

    def __str__(self):
        return self.message

class UnsupportedTypeException(BioQcMetricsException):
    """Exception thrown when tool encounters an unsupported type"""
    def __init__(self, message):
        self.message = message 

    def __str__(self):
        return self.message

class ClassNotFoundException(BioQcMetricsException):
    """Exception thrown when tool is unable to locate a class""" 
    def __init__(self, message):
        self.message = message 

    def __str__(self):
        return self.message

class DuplicateInputException(BioQcMetricsException):
    """Exception thrown when a QC tool encounters duplicate inputs""" 
    def __init__(self, message):
        self.message = message 

    def __str__(self):
        return self.message
