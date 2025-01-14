# Licensed under the GPL: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
# For details: https://github.com/PyCQA/pylint/blob/main/LICENSE
# Copyright (c) https://github.com/PyCQA/pylint/blob/main/CONTRIBUTORS.txt

from __future__ import annotations

import contextlib
import sys
import traceback
from collections.abc import Iterator, Sequence
from datetime import datetime
from pathlib import Path

from astroid import modutils

from pylint.config import PYLINT_HOME
from pylint.lint.expand_modules import get_python_path


def prepare_crash_report(ex: Exception, filepath: str, crash_file_path: str) -> Path:
    issue_template_path = (
        Path(PYLINT_HOME) / datetime.now().strftime(str(crash_file_path))
    ).resolve()
    with open(filepath, encoding="utf8") as f:
        file_content = f.read()
    template = ""
    if not issue_template_path.exists():
        template = """\
First, please verify that the bug is not already filled:
https://github.com/PyCQA/pylint/issues/

Then create a new crash issue:
https://github.com/PyCQA/pylint/issues/new?assignees=&labels=crash%2Cneeds+triage&template=BUG-REPORT.yml

"""
    template += f"""\

Issue title:
Crash ``{ex}`` (if possible, be more specific about what made pylint crash)
Content:
When parsing the following file:

<!--
 If sharing the code is not an option, please state so,
 but providing only the stacktrace would still be helpful.
 -->

```python
{file_content}
```

pylint crashed with a ``{ex.__class__.__name__}`` and with the following stacktrace:
```
"""
    template += traceback.format_exc()
    template += "```\n"
    try:
        with open(issue_template_path, "a", encoding="utf8") as f:
            f.write(template)
    except Exception as exc:  # pylint: disable=broad-except
        print(
            f"Can't write the issue template for the crash in {issue_template_path} "
            f"because of: '{exc}'\nHere's the content anyway:\n{template}."
        )
    return issue_template_path


def get_fatal_error_message(filepath: str, issue_template_path: Path) -> str:
    return (
        f"Fatal error while checking '{filepath}'. "
        f"Please open an issue in our bug tracker so we address this. "
        f"There is a pre-filled template that you can use in '{issue_template_path}'."
    )


def _is_part_of_namespace_package(filename: str) -> bool:
    """Check if a file is part of a namespace package."""
    try:
        modname = modutils.modpath_from_file(filename)
    except ImportError:
        modname = [Path(filename).stem]

    try:
        spec = modutils.file_info_from_modpath(modname)
    except ImportError:
        return False

    return modutils.is_namespace(spec)


def _patch_sys_path(args: Sequence[str]) -> list[str]:
    original = list(sys.path)
    changes = []
    seen = set()
    for arg in args:
        path = get_python_path(arg)
        if _is_part_of_namespace_package(path):
            continue
        if path not in seen:
            changes.append(path)
            seen.add(path)

    sys.path[:] = changes + sys.path
    return original


@contextlib.contextmanager
def fix_import_path(args: Sequence[str]) -> Iterator[None]:
    """Prepare 'sys.path' for running the linter checks.

    Within this context, each of the given arguments is importable.
    Paths are added to 'sys.path' in corresponding order to the arguments.
    We avoid adding duplicate directories to sys.path.
    `sys.path` is reset to its original value upon exiting this context.
    """
    original = _patch_sys_path(args)
    try:
        yield
    finally:
        sys.path[:] = original
