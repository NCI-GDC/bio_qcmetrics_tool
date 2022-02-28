import os
import sys
from contextlib import contextmanager
from io import StringIO
from typing import TYPE_CHECKING, Generator, List, Tuple

from bio_qcmetrics_tool.utils.logger import Logger

if TYPE_CHECKING:
    from sqlite3 import Cursor


@contextmanager
def captured_output() -> Generator[Tuple[StringIO, StringIO], None, None]:
    """Captures stderr and stdout and returns them"""
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        Logger.setup_root_logger()
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def get_test_data_path(fname: str) -> str:
    """
    Helper function to get full path to a test
    dataset give the basename.
    :param fname: test dataset file basename
    """
    path = os.path.join(os.path.dirname(__file__), "data/{0}".format(fname))
    return path


def get_table_list(cur: 'Cursor') -> list:
    """
    Gets a list of tables in the sqlite db provided the cursor.
    """
    res = cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    rows = list([i[0] for i in list(res.fetchall())])
    return rows


def cleanup_files(files: List[str]) -> None:
    """
    Takes a file or a list of files and removes them.
    """

    flist = []
    if isinstance(files, list):
        flist = files[:]
    else:
        flist = [files]

    for fil in flist:
        if os.path.exists(fil):
            os.remove(fil)
