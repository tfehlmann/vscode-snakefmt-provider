# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Implementation of tool support over LSP."""
from __future__ import annotations

import copy
import difflib
import json
import os
import pathlib
import re
import sys
import sysconfig
import traceback
from typing import Any, Dict, Optional, Sequence


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


# **********************************************************
# Update PATH before running anything.
# **********************************************************
def update_environ_path() -> None:
    """Update PATH environment variable with the 'scripts' directory.
    Windows: .venv/Scripts
    Linux/MacOS: .venv/bin
    """
    scripts = sysconfig.get_path("scripts")
    paths_variants = ["Path", "PATH"]

    for var_name in paths_variants:
        if var_name in os.environ:
            paths = os.environ[var_name].split(os.pathsep)
            if scripts not in paths:
                paths.insert(0, scripts)
                os.environ[var_name] = os.pathsep.join(paths)
                break


# Ensure that we can import LSP libraries, and other bundled libraries.
BUNDLE_DIR = pathlib.Path(__file__).parent.parent
# Always use bundled server files.
update_sys_path(os.fspath(BUNDLE_DIR / "tool"), "useBundled")
update_sys_path(
    os.fspath(BUNDLE_DIR / "libs"),
    os.getenv("LS_IMPORT_STRATEGY", "useBundled"),
)
update_environ_path()

# **********************************************************
# Imports needed for the language server goes below this.
# **********************************************************
# pylint: disable=wrong-import-position,import-error
import jsonrpc
import lsprotocol.types as lsp
import utils
from pygls import server, uris, workspace

WORKSPACE_SETTINGS = {}
GLOBAL_SETTINGS = {}
RUNNER = pathlib.Path(__file__).parent / "runner.py"

MAX_WORKERS = 5
LSP_SERVER = server.LanguageServer(
    name="snakefmt-server", version="0.1.0", max_workers=MAX_WORKERS
)


# **********************************************************
# Tool specific code goes below this.
# **********************************************************

# Reference:
#  LS Protocol:
#  https://microsoft.github.io/language-server-protocol/specifications/specification-3-16/
#
#  Sample implementations:
#  Pylint: https://github.com/microsoft/vscode-pylint/blob/main/bundled/tool
#  Black: https://github.com/microsoft/vscode-black-formatter/blob/main/bundled/tool
#  isort: https://github.com/microsoft/vscode-isort/blob/main/bundled/formatter

from black import find_pyproject_toml

TOOL_MODULE = "snakefmt"
TOOL_DISPLAY = "Snakefmt"

TOOL_ARGS = []  # default arguments always passed to your tool.

MIN_VERSION = "0.1.0"


# **********************************************************
# Linting features start here
# **********************************************************

#  See `pylint` implementation for a full featured linter extension:
#  Pylint: https://github.com/microsoft/vscode-pylint/blob/main/bundled/tool


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
def did_open(params: lsp.DidOpenTextDocumentParams) -> None:
    """LSP handler for textDocument/didOpen request."""
    document = LSP_SERVER.workspace.get_document(params.text_document.uri)
    diagnostics: list[lsp.Diagnostic] = _linting_helper(document)
    LSP_SERVER.publish_diagnostics(document.uri, diagnostics)


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_SAVE)
def did_save(params: lsp.DidSaveTextDocumentParams) -> None:
    """LSP handler for textDocument/didSave request."""
    document = LSP_SERVER.workspace.get_document(params.text_document.uri)
    diagnostics: list[lsp.Diagnostic] = _linting_helper(document)
    LSP_SERVER.publish_diagnostics(document.uri, diagnostics)


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
def did_close(params: lsp.DidCloseTextDocumentParams) -> None:
    """LSP handler for textDocument/didClose request."""
    document = LSP_SERVER.workspace.get_document(params.text_document.uri)
    # Publishing empty diagnostics to clear the entries for this file.
    LSP_SERVER.publish_diagnostics(document.uri, [])


def slugify(string: str) -> str:
    """Convert camel case to slug case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "-", string).lower()


def try_handle_black_error(
    error_message: str, error: str, document: workspace.Document
) -> Optional[list[lsp.Diagnostic]]:
    """Try to handle black error."""
    error_message_match2 = re.search("```\n?(.+)\n?```", error_message)
    if error_message_match2:
        black_error_message = error_message_match2.group(1)
    else:
        black_error_message = error.splitlines()[2]
    # try to find line number
    line_match = re.match(r"Cannot parse: (\d+)", black_error_message, re.UNICODE)
    if line_match:
        line_number = int(line_match.group(1)) - 1
        line_start = len(
            re.match(r"\s*", document.lines[line_number], re.UNICODE).group(0)
        )
        line_end = len(document.lines[line_number])
        return [
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=line_number, character=line_start),
                    end=lsp.Position(line=line_number, character=line_end),
                ),
                message=f"InvalidPython: Black error:\n{black_error_message}",
                severity=lsp.DiagnosticSeverity.Error,
                code="snakefmt:black-error:invalid-python",
                source=TOOL_DISPLAY,
            )
        ]
    return None


def try_handle_snakefmt_error(
    error_message: str, document: workspace.Document
) -> Optional[list[lsp.Diagnostic]]:
    """Try to handle snakefmt error."""
    # snakefmt uses a format like "ExceptionName: (L?)X"
    serr_result = re.match(r"(\w+): L?(\d+):?(.*)", error_message, re.DOTALL)
    if not serr_result:
        return None
    exception_name = serr_result.group(1)
    line_number = int(serr_result.group(2)) - 1
    line_start = len(re.match(r"\s*", document.lines[line_number], re.UNICODE).group(0))
    line_end = len(document.lines[line_number])
    end_pos = lsp.Position(line=line_number, character=line_end)
    code_error = serr_result.group(3).strip()
    if code_error:
        # try to find last line affected by error
        last_code_error_lines = code_error.splitlines()
        n_err_lines = len(last_code_error_lines)
        if n_err_lines > 1:
            for line_num in range(line_number + 1, line_number + n_err_lines + 1):
                if (
                    difflib.SequenceMatcher(
                        lambda x: x == " ",
                        document.lines[line_num].rstrip(),
                        last_code_error_lines[-1],
                    ).ratio()
                    > 0.9
                ):
                    end_pos = lsp.Position(
                        line=line_num, character=len(document.lines[line_num])
                    )
                    break

    return [
        lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=line_number, character=line_start),
                end=end_pos,
            ),
            message=error_message,
            severity=lsp.DiagnosticSeverity.Error,
            code=f"snakefmt:{slugify(exception_name)}",
            source=TOOL_DISPLAY,
        )
    ]


def parse_formatting_error(
    error: str, document: workspace.Document
) -> list[lsp.Diagnostic]:
    """Parse formatting error from snakefmt output and return a list of diagnostics."""
    error_message_match = re.match(
        r'\[ERROR\] In file ".+":  (.+)[\r\n]+\[INFO', error, re.DOTALL
    )
    if error_message_match:
        error_message = error_message_match.group(1).strip()
        if error_message.startswith("InvalidPython: Black error:"):
            black_res = try_handle_black_error(error_message, error, document)
            if black_res:
                return black_res

        res = try_handle_snakefmt_error(error_message, document)
        if res:
            return res
    return [
        lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=0, character=0),
            ),
            message="An unexpected error occurred, Snakefmt could not format this document.",
            severity=lsp.DiagnosticSeverity.Warning,
            code="snakefmt:unexpected-error",
            source=TOOL_DISPLAY,
        )
    ]


def _linting_helper(document: workspace.Document) -> list[lsp.Diagnostic]:
    try:
        settings = _get_settings_by_document(document)
        if settings["disableLinting"]:
            return []
        if document.language_id == "python" and not settings["enablePythonLinting"]:
            return []
        result = _run_tool_on_document(document, extra_args=["--check"])
        if not result.stderr.startswith("[ERROR]"):
            LSP_SERVER.show_message_log(
                f"Successfully linted {document.uri}",
                lsp.MessageType.Info,
            )
        else:
            return parse_formatting_error(result.stderr, document)

        rng = lsp.Range(
            start=lsp.Position(line=0, character=0),
            end=lsp.Position(line=0, character=0),
        )
        return (
            []
            if "unchanged" in result.stderr
            else [
                lsp.Diagnostic(
                    range=rng,
                    message="Document is not following snakefmt formatting",
                    severity=lsp.DiagnosticSeverity.Information,
                    code="snakefmt:not-formatted",
                    source=TOOL_DISPLAY,
                )
            ]
        )
    except Exception:  # pylint: disable=broad-except
        LSP_SERVER.show_message_log(
            f"Linting failed with error:\r\n{traceback.format_exc()}\n\n",
            lsp.MessageType.Error,
        )
    return []


# **********************************************************
# Linting features end here
# **********************************************************

# **********************************************************
# Formatting features start here
# **********************************************************
#  Sample implementations:
#  Black: https://github.com/microsoft/vscode-black-formatter/blob/main/bundled/tool


@LSP_SERVER.feature(lsp.TEXT_DOCUMENT_FORMATTING)
def formatting(params: lsp.DocumentFormattingParams) -> list[lsp.TextEdit] | None:
    """LSP handler for textDocument/formatting request."""
    document = LSP_SERVER.workspace.get_document(params.text_document.uri)
    edits = _formatting_helper(document)
    if edits:
        return edits

    # NOTE: If you provide [] array, VS Code will clear the file of all contents.
    # To indicate no changes to file return None.
    return None


def _formatting_helper(document: workspace.Document) -> list[lsp.TextEdit] | None:
    result = _run_tool_on_document(document, use_stdin=True)
    if result.stdout:
        new_source = _match_line_endings(document, result.stdout)
        return [
            lsp.TextEdit(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=len(document.lines), character=0),
                ),
                new_text=new_source,
            )
        ]
    return None


def _get_line_endings(lines: list[str]) -> str:
    """Returns line endings used in the text."""
    try:
        if lines[0][-2:] == "\r\n":
            return "\r\n"
        return "\n"
    except Exception:  # pylint: disable=broad-except
        return None


def _match_line_endings(document: workspace.Document, text: str) -> str:
    """Ensures that the edited text line endings matches the document line endings."""
    expected = _get_line_endings(document.source.splitlines(keepends=True))
    actual = _get_line_endings(text.splitlines(keepends=True))
    if actual == expected or actual is None or expected is None:
        return text
    return text.replace(actual, expected)


# **********************************************************
# Formatting features ends here
# **********************************************************


# **********************************************************
# Required Language Server Initialization and Exit handlers.
# **********************************************************
@LSP_SERVER.feature(lsp.INITIALIZE)
def initialize(params: lsp.InitializeParams) -> None:
    """LSP handler for initialize request."""
    log_to_output(f"CWD Server: {os.getcwd()}")

    GLOBAL_SETTINGS.update(**params.initialization_options.get("globalSettings", {}))

    settings = params.initialization_options["settings"]
    _update_workspace_settings(settings)
    log_to_output(
        f"Settings used to run Server:\r\n{json.dumps(settings, indent=4, ensure_ascii=False)}\r\n"
    )
    log_to_output(
        f"Global settings:\r\n{json.dumps(GLOBAL_SETTINGS, indent=4, ensure_ascii=False)}\r\n"
    )

    paths = "\r\n   ".join(sys.path)
    log_to_output(f"sys.path used to run Server:\r\n   {paths}")

    _log_version_info()


@LSP_SERVER.feature(lsp.EXIT)
def on_exit(_params: Optional[Any] = None) -> None:
    """Handle clean up on exit."""
    jsonrpc.shutdown_json_rpc()


@LSP_SERVER.feature(lsp.SHUTDOWN)
def on_shutdown(_params: Optional[Any] = None) -> None:
    """Handle clean up on shutdown."""
    jsonrpc.shutdown_json_rpc()


def _log_version_info() -> None:
    for value in WORKSPACE_SETTINGS.values():
        try:
            from packaging.version import parse as parse_version

            settings = copy.deepcopy(value)
            result = _run_tool(["--version"], settings)
            code_workspace = settings["workspaceFS"]
            log_to_output(
                f"Version info for formatter running for {code_workspace}:\r\n{result.stdout}"
            )

            # This is text we get from running `snakefmt --version`
            # snakefmt, version 0.6.1 <--- This is the version we want.
            first_line = result.stdout.splitlines(keepends=False)[0]
            current_version = first_line.split(" ")[-1]

            version = parse_version(current_version)
            min_version = parse_version(MIN_VERSION)

            if version < min_version:
                log_error(
                    f"Version of formatter running for {code_workspace} is NOT supported:\r\n"
                    f"SUPPORTED {TOOL_MODULE}>={min_version}\r\n"
                    f"FOUND {TOOL_MODULE}=={current_version}\r\n"
                )
            else:
                log_to_output(
                    f"SUPPORTED {TOOL_MODULE}>={min_version}\r\n"
                    f"FOUND {TOOL_MODULE}=={current_version}\r\n"
                )
        except:  # pylint: disable=bare-except
            log_to_output(
                f"Error while detecting snakefmt version:\r\n{traceback.format_exc()}"
            )


# *****************************************************
# Internal functional and settings management APIs.
# *****************************************************
def _get_global_defaults():
    return {
        "path": GLOBAL_SETTINGS.get("path", []),
        "interpreter": GLOBAL_SETTINGS.get("interpreter", [sys.executable]),
        "args": GLOBAL_SETTINGS.get("args", []),
        "importStrategy": GLOBAL_SETTINGS.get("importStrategy", "useBundled"),
        "showNotifications": GLOBAL_SETTINGS.get("showNotifications", "off"),
        "disableLinting": GLOBAL_SETTINGS.get("disableLinting", False),
        "enablePythonLinting": GLOBAL_SETTINGS.get("enablePythonLinting", True),
        "config": GLOBAL_SETTINGS.get("config", ""),
        "executable": GLOBAL_SETTINGS.get("executable", ""),
    }


def _update_workspace_settings(settings):
    if not settings:
        key = utils.normalize_path(os.getcwd())
        WORKSPACE_SETTINGS[key] = {
            "cwd": key,
            "workspaceFS": key,
            "workspace": uris.from_fs_path(key),
            **_get_global_defaults(),
        }
        return

    for setting in settings:
        key = utils.normalize_path(uris.to_fs_path(setting["workspace"]))
        WORKSPACE_SETTINGS[key] = {
            **setting,
            "workspaceFS": key,
        }


def _get_settings_by_path(file_path: pathlib.Path):
    workspaces = {s["workspaceFS"] for s in WORKSPACE_SETTINGS.values()}

    while file_path != file_path.parent:
        str_file_path = utils.normalize_path(file_path)
        if str_file_path in workspaces:
            return WORKSPACE_SETTINGS[str_file_path]
        file_path = file_path.parent

    setting_values = list(WORKSPACE_SETTINGS.values())
    return setting_values[0]


def _get_document_key(document: workspace.Document):
    if WORKSPACE_SETTINGS:
        document_workspace = pathlib.Path(document.path)
        workspaces = {s["workspaceFS"] for s in WORKSPACE_SETTINGS.values()}

        # Find workspace settings for the given file.
        while document_workspace != document_workspace.parent:
            norm_path = utils.normalize_path(document_workspace)
            if norm_path in workspaces:
                return norm_path
            document_workspace = document_workspace.parent

    return None


def _get_settings_by_document(document: workspace.Document | None):
    if document is None or document.path is None:
        return list(WORKSPACE_SETTINGS.values())[0]

    key = _get_document_key(document)
    if key is None:
        # This is either a non-workspace file or there is no workspace.
        key = utils.normalize_path(pathlib.Path(document.path).parent)
        return {
            "cwd": key,
            "workspaceFS": key,
            "workspace": uris.from_fs_path(key),
            **_get_global_defaults(),
        }

    return WORKSPACE_SETTINGS[str(key)]


# *****************************************************
# Internal execution APIs.
# *****************************************************
def get_cwd(settings: Dict[str, Any], document: Optional[workspace.Document]) -> str:
    """Returns cwd for the given settings and document."""
    if settings["cwd"] == "${workspaceFolder}":
        return settings["workspaceFS"]

    if settings["cwd"] == "${fileDirname}":
        if document is not None:
            return os.fspath(pathlib.Path(document.path).parent)
        return settings["workspaceFS"]

    return settings["cwd"]


# pylint: disable=too-many-branches,too-many-statements
def _run_tool_on_document(
    document: workspace.Document,
    use_stdin: bool = False,
    extra_args: Sequence[str] = None,
) -> utils.RunResult | None:
    """Runs tool on the given document.

    if use_stdin is true then contents of the document is passed to the
    tool via stdin.
    """
    if extra_args is None:
        extra_args = []
    # deep copy here to prevent accidentally updating global settings.
    settings = copy.deepcopy(_get_settings_by_document(document))

    code_workspace = settings["workspaceFS"]
    cwd = get_cwd(settings, document)

    use_path = False
    use_rpc = False
    if settings["executable"] and len(settings["path"]) == 0:
        settings["path"] = [settings["executable"]]
    if settings["path"]:
        # 'path' setting takes priority over everything.
        use_path = True
        argv = settings["path"]
    elif settings["interpreter"] and not utils.is_current_interpreter(
        settings["interpreter"][0]
    ):
        # If there is a different interpreter set use JSON-RPC to the subprocess
        # running under that interpreter.
        argv = [TOOL_MODULE]
        use_rpc = True
    else:
        # if the interpreter is same as the interpreter running this
        # process then run as module.
        argv = [TOOL_MODULE]

    # check if config is provided by --args
    if not any(arg.startswith("--config") for arg in settings["args"]):
        # config provided over config parameter?
        config_file = (
            settings["config"]
            if "config" in settings and settings["config"]
            else find_pyproject_toml((document.path,))
        )
        if config_file:
            settings["args"].append("--config")
            settings["args"].append(config_file)

    argv += TOOL_ARGS + settings["args"] + extra_args

    if use_stdin:
        argv += ["-"]
    else:
        argv += [document.path]

    if use_path:
        # This mode is used when running executables.
        log_to_output(" ".join(argv))
        log_to_output(f"CWD Server: {cwd}")
        result = utils.run_path(
            argv=argv,
            use_stdin=use_stdin,
            cwd=cwd,
            source=document.source.replace("\r\n", "\n"),
        )
        if result.stderr:
            log_to_output(result.stderr)
    elif use_rpc:
        # This mode is used if the interpreter running this server is different from
        # the interpreter used for running this server.
        log_to_output(" ".join(settings["interpreter"] + ["-m"] + argv))
        log_to_output(f"CWD formatter: {cwd}")

        result = jsonrpc.run_over_json_rpc(
            workspace=code_workspace,
            interpreter=settings["interpreter"],
            module=TOOL_MODULE,
            argv=argv,
            use_stdin=use_stdin,
            cwd=cwd,
            source=document.source,
            env={
                "LS_IMPORT_STRATEGY": settings["importStrategy"],
            },
        )
        result = _to_run_result_with_logging(result)
    else:
        # In this mode the tool is run as a module in the same process as the language server.
        log_to_output(" ".join([sys.executable, "-m"] + argv))
        log_to_output(f"CWD formatter: {cwd}")
        # This is needed to preserve sys.path, in cases where the tool modifies
        # sys.path and that might not work for this scenario next time around.
        with utils.substitute_attr(sys, "path", [""] + sys.path[:]):
            try:
                result = utils.run_module(
                    module=TOOL_MODULE,
                    argv=argv,
                    use_stdin=use_stdin,
                    cwd=cwd,
                    source=document.source,
                )
            except Exception:
                log_error(traceback.format_exc(chain=True))
                raise
        if result.stderr:
            log_to_output(result.stderr)

    log_to_output(f"{document.uri} :\r\n{result.stdout}")
    return result


def _run_tool(extra_args: Sequence[str], settings: Dict[str, Any]) -> utils.RunResult:
    """Runs tool."""
    code_workspace = settings["workspaceFS"]
    cwd = get_cwd(settings, None)

    use_path = False
    use_rpc = False
    if settings["executable"] and len(settings["path"]) == 0:
        settings["path"] = [settings["executable"]]
    if len(settings["path"]) > 0:
        # 'path' setting takes priority over everything.
        use_path = True
        argv = settings["path"]
    elif len(settings["interpreter"]) > 0 and not utils.is_current_interpreter(
        settings["interpreter"][0]
    ):
        # If there is a different interpreter set use JSON-RPC to the subprocess
        # running under that interpreter.
        argv = [TOOL_MODULE]
        use_rpc = True
    else:
        # if the interpreter is same as the interpreter running this
        # process then run as module.
        argv = [TOOL_MODULE]

    argv += extra_args

    if use_path:
        # This mode is used when running executables.
        log_to_output(" ".join(argv))
        log_to_output(f"CWD Server: {cwd}")
        result = utils.run_path(argv=argv, use_stdin=True, cwd=cwd)
        if result.stderr:
            log_to_output(result.stderr)
    elif use_rpc:
        # This mode is used if the interpreter running this server is different from
        # the interpreter used for running this server.
        log_to_output(" ".join(settings["interpreter"] + ["-m"] + argv))
        log_to_output(f"CWD formatter: {cwd}")
        result = jsonrpc.run_over_json_rpc(
            workspace=code_workspace,
            interpreter=settings["interpreter"],
            module=TOOL_MODULE,
            argv=argv,
            use_stdin=True,
            cwd=cwd,
            env={
                "LS_IMPORT_STRATEGY": settings["importStrategy"],
            },
        )
        result = _to_run_result_with_logging(result)
    else:
        # In this mode the tool is run as a module in the same process as the language server.
        log_to_output(" ".join([sys.executable, "-m"] + argv))
        log_to_output(f"CWD formatter: {cwd}")
        # This is needed to preserve sys.path, in cases where the tool modifies
        # sys.path and that might not work for this scenario next time around.
        with utils.substitute_attr(sys, "path", [""] + sys.path[:]):
            try:
                result = utils.run_module(
                    module=TOOL_MODULE, argv=argv, use_stdin=True, cwd=cwd
                )
            except Exception:
                log_error(traceback.format_exc(chain=True))
                raise
        if result.stderr:
            log_to_output(result.stderr)

    if LSP_SERVER.lsp.trace == lsp.TraceValues.Verbose:
        log_to_output(f"\r\n{result.stdout}\r\n")

    return result


def _to_run_result_with_logging(rpc_result: jsonrpc.RpcRunResult) -> utils.RunResult:
    error = ""
    if rpc_result.exception:
        log_error(rpc_result.exception)
        error = rpc_result.exception
    elif rpc_result.stderr:
        log_to_output(rpc_result.stderr)
        error = rpc_result.stderr
    return utils.RunResult(rpc_result.stdout, error)


# *****************************************************
# Logging and notification.
# *****************************************************
def log_to_output(
    message: str, msg_type: lsp.MessageType = lsp.MessageType.Log
) -> None:
    """Logs messages to Output > Snakefmt Formatter channel only."""
    LSP_SERVER.show_message_log(message, msg_type)


def log_error(message: str) -> None:
    """Logs messages with notification on error."""
    LSP_SERVER.show_message_log(message, lsp.MessageType.Error)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["onError", "onWarning", "always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Error)


def log_warning(message: str) -> None:
    """Logs messages with notification on warning."""
    LSP_SERVER.show_message_log(message, lsp.MessageType.Warning)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["onWarning", "always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Warning)


def log_always(message: str) -> None:
    """Logs messages with notification."""
    LSP_SERVER.show_message_log(message, lsp.MessageType.Info)
    if os.getenv("LS_SHOW_NOTIFICATION", "off") in ["always"]:
        LSP_SERVER.show_message(message, lsp.MessageType.Info)


# *****************************************************
# Start the server.
# *****************************************************
if __name__ == "__main__":
    LSP_SERVER.start_io()
