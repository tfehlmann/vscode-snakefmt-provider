# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Runner to use when running under a different interpreter.
"""

import os
import pathlib
import platform
import sys
import sysconfig
import traceback


# **********************************************************
# Update sys.path before importing any bundled libraries.
# **********************************************************
def update_sys_path(path_to_add: str, strategy: str) -> None:
    """Add given path to `sys.path`."""
    if path_to_add not in sys.path and os.path.isdir(path_to_add):
        if strategy == "useBundled":
            sys.path.insert(0, path_to_add)
        else:
            sys.path.append(path_to_add)


def get_bundled_scripts_dir() -> pathlib.Path | None:
    """Return bundled executable directory for the current platform."""
    machine = platform.machine().lower()
    if machine in {"amd64", "x86_64"}:
        arch = "x64"
    elif machine in {"aarch64", "arm64"}:
        arch = "arm64"
    else:
        return None

    if sys.platform.startswith("linux"):
        os_name = "linux"
    elif sys.platform == "darwin":
        os_name = "darwin"
    elif sys.platform == "win32":
        os_name = "win32"
    else:
        return None

    return BUNDLE_DIR / "libs" / "bin" / f"{os_name}-{arch}"


def update_environ_path() -> None:
    """Update PATH with bundled executables and interpreter scripts."""
    candidate_paths = [
        get_bundled_scripts_dir(),
        pathlib.Path(sysconfig.get_path("scripts")),
    ]
    paths_to_add = [
        os.fspath(candidate)
        for candidate in candidate_paths
        if candidate is not None and candidate.is_dir()
    ]
    if not paths_to_add:
        return

    var_name = "Path" if "Path" in os.environ else "PATH"
    paths = os.environ.get(var_name, "").split(os.pathsep)
    for path_to_add in reversed(paths_to_add):
        if path_to_add not in paths:
            paths.insert(0, path_to_add)
    os.environ[var_name] = os.pathsep.join(path for path in paths if path)


# Ensure that we can import LSP libraries, and other bundled libraries.
BUNDLE_DIR = pathlib.Path(__file__).parent.parent
# Always use bundled server files.
update_sys_path(os.fspath(BUNDLE_DIR / "tool"), "useBundled")
update_sys_path(
    os.fspath(BUNDLE_DIR / "libs"),
    os.getenv("LS_IMPORT_STRATEGY", "useBundled"),
)
update_environ_path()


# pylint: disable=wrong-import-position,import-error
import jsonrpc
import utils

RPC = jsonrpc.create_json_rpc(sys.stdin.buffer, sys.stdout.buffer)

EXIT_NOW = False  # pylint: disable=invalid-name
while not EXIT_NOW:
    msg = RPC.receive_data()

    method = msg["method"]
    if method == "exit":
        EXIT_NOW = True  # pylint: disable=invalid-name
        continue

    if method == "run":
        IS_EXCEPTION = False  # pylint: disable=invalid-name
        # This is needed to preserve sys.path, pylint modifies
        # sys.path and that might not work for this scenario
        # next time around.
        with utils.substitute_attr(sys, "path", [""] + sys.path[:]):
            try:
                result = utils.run_module(
                    module=msg["module"],
                    argv=msg["argv"],
                    use_stdin=msg["useStdin"],
                    cwd=msg["cwd"],
                    source=msg["source"] if "source" in msg else None,
                )
            except Exception:  # pylint: disable=broad-except
                result = utils.RunResult("", traceback.format_exc(chain=True))
                IS_EXCEPTION = True  # pylint: disable=invalid-name

        response = {"id": msg["id"], "error": result.stderr}
        if IS_EXCEPTION:
            response["exception"] = IS_EXCEPTION
        elif result.stdout:
            response["result"] = result.stdout

        RPC.send_data(response)
