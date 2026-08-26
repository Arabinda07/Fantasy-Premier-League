"""Cross-platform Atomic File Writing & Concurrency Safety Utilities.

Provides atomic JSON and CSV writing using tempfile + os.replace, ensuring that
concurrent daemon processes (e.g. pipeline automation) never expose half-written files
to readers (e.g. Vite frontend dev server, live matchday loaders).
"""
import contextlib
import json
import os
import tempfile
from typing import Any, Dict, Generator, Union
import pandas as pd


def atomic_write_json(filepath: str, data: Union[Dict[str, Any], list], indent: int = 2) -> None:
    """Write JSON data atomically: serialize to a tempfile in the same directory, then rename into place."""
    dir_name = os.path.dirname(filepath)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(suffix='.json.tmp', dir=dir_name or None)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as tmp_f:
            json.dump(data, tmp_f, indent=indent)
        os.replace(tmp_path, filepath)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def atomic_write_csv(filepath: str, df: pd.DataFrame, index: bool = False) -> None:
    """Write DataFrame to CSV atomically: write to a tempfile in the same directory, then rename into place."""
    dir_name = os.path.dirname(filepath)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(suffix='.csv.tmp', dir=dir_name or None)
    try:
        os.close(fd)  # Close raw file descriptor so pandas can open it safely
        df.to_csv(tmp_path, index=index, encoding='utf-8')
        os.replace(tmp_path, filepath)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


@contextlib.contextmanager
def locked_file_transaction(filepath: str) -> Generator[str, None, None]:
    """Context manager providing simple atomic staging path for file writing."""
    dir_name = os.path.dirname(filepath)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(suffix='.lock.tmp', dir=dir_name or None)
    os.close(fd)
    try:
        yield tmp_path
        os.replace(tmp_path, filepath)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
