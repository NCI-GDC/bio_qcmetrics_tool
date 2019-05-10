"""Module containing general utilities for parsing"""

def parse_type(item, na=None):
    """
    Attempts to parse a string into basic python types.
    """
    value = None

    try:
        if not item:
            value = na 
        elif '.' in item:
            value = float(item)
        else:
            value = int(item) 
    except ValueError:
        value = item

    return value
