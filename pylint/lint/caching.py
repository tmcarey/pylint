# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/main/LICENSE
# Copyright (c) https://github.com/PyCQA/pylint/blob/main/CONTRIBUTORS.txt

from __future__ import annotations

import pickle
import sys
import warnings
from pathlib import Path

from pylint.constants import PYLINT_HOME
from pylint.utils import LinterStats


def _get_pdata_path(
    base_name: Path, recurs: int, pylint_home: Path = Path(PYLINT_HOME)
) -> Path:
    underscored_name = "_".join(str(p) for p in base_name.parents)
    return pylint_home / f"{underscored_name}{recurs}.stats"


def load_results(
    base: str | Path, pylint_home: str | Path = PYLINT_HOME
) -> LinterStats | None:
    base = Path(base)
    pylint_home = Path(pylint_home)
    data_file = _get_pdata_path(base, 1, pylint_home)
    try:
        with open(data_file, "rb") as stream:
            data = pickle.load(stream)
            if not isinstance(data, LinterStats):
                warnings.warn(
                    "You're using an old pylint cache with invalid data following "
                    f"an upgrade, please delete '{data_file}'.",
                    UserWarning,
                )
                return None
            return data
    except Exception:  # pylint: disable=broad-except
        # There's probably an issue with the cache but we don't know how to fix it
        return None


def save_results(
    results: LinterStats, base: str | Path, pylint_home: str | Path = PYLINT_HOME
) -> None:
    base = Path(base)
    pylint_home = Path(pylint_home)
    if not pylint_home.exists():
        try:
            pylint_home.mkdir(exist_ok=True)
        except OSError:
            print(f"Unable to create directory {pylint_home}", file=sys.stderr)
    data_file = _get_pdata_path(base, 1)
    try:
        with open(data_file, "wb") as stream:
            pickle.dump(results, stream)
    except OSError as ex:
        print(f"Unable to create file {data_file}: {ex}", file=sys.stderr)