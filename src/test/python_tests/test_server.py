# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""
Test for linting over LSP.
"""
import difflib
from threading import Event

from hamcrest import assert_that, is_

from .lsp_test_client import constants, defaults, session, utils

SERVER_INFO = utils.get_server_info_defaults()
TIMEOUT = 10  # 10 seconds


def test_linting():
    """Test to linting on file open."""
    test_file_path = constants.TEST_DATA / "sample1" / "toFormat.smk"
    test_file_uri = utils.as_uri(str(test_file_path))
    contents = test_file_path.read_text()

    actual = []

    with session.LspSession() as ls_session:
        ls_session.initialize(defaults.VSCODE_DEFAULT_INITIALIZE)

        done = Event()

        def _handler(params):
            nonlocal actual
            actual = params
            done.set()

        ls_session.set_notification_callback(session.PUBLISH_DIAGNOSTICS, _handler)

        ls_session.notify_did_open(
            {
                "textDocument": {
                    "uri": test_file_uri,
                    "languageId": "snakemake",
                    "version": 1,
                    "text": contents,
                }
            }
        )

        # wait for some time to receive all notifications
        done.wait(TIMEOUT)

    expected = {
        "uri": test_file_uri,
        "diagnostics": [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 0},
                },
                "message": "Document is not following snakefmt formatting",
                "severity": 3,
                "code": "snakefmt:not-formatted",
                "source": SERVER_INFO["module"],
            },
        ],
    }

    assert_that(actual, is_(expected))


def test_formatting():
    """Test formatting a snakemake file."""
    formatted_test_file_path = constants.TEST_DATA / "sample1" / "formatted.smk"
    unformatted_test_file_path = constants.TEST_DATA / "sample1" / "toFormat.smk"

    contents = unformatted_test_file_path.read_text("utf-8")
    lines = contents.splitlines(keepends=False)

    actual = []
    with utils.SnakemakeFile(contents, unformatted_test_file_path.parent) as file:
        uri = utils.as_uri(str(file))

        with session.LspSession() as ls_session:
            ls_session.initialize()
            ls_session.notify_did_open(
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "snakemake",
                        "version": 1,
                        "text": contents,
                    }
                }
            )
            actual = ls_session.text_document_formatting(
                {
                    "textDocument": {"uri": uri},
                    "options": {"tabSize": 4, "insertSpaces": True},
                }
            )

    expected = [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": len(lines), "character": 0},
            },
            "newText": formatted_test_file_path.read_text("utf-8"),
        }
    ]

    diff = difflib.unified_diff(
        expected[0]["newText"].splitlines(),
        actual[0]["newText"].splitlines(),
        fromfile="expected",
        tofile="actual",
    )

    assert_that(actual, is_(expected), "\n".join(diff))


def test_formatting_with_custom_config():
    """Test formatting a snakemake file and providing a custom config file."""
    formatted_test_file_path = constants.TEST_DATA / "sample2" / "formatted.smk"
    unformatted_test_file_path = constants.TEST_DATA / "sample2" / "toFormat.smk"
    config_file = constants.TEST_DATA / "sample2" / "config.toml"

    contents = unformatted_test_file_path.read_text("utf-8")
    lines = contents.splitlines(keepends=False)

    actual = []
    with utils.SnakemakeFile(contents, unformatted_test_file_path.parent) as file:
        uri = utils.as_uri(str(file))

        with session.LspSession() as ls_session:
            init_options = defaults.VSCODE_DEFAULT_INITIALIZE["initializationOptions"]
            init_options["settings"][0]["args"] = [
                "--config",
                str(config_file),
            ]
            ls_session.initialize(defaults.VSCODE_DEFAULT_INITIALIZE)
            ls_session.notify_did_open(
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "snakemake",
                        "version": 1,
                        "text": contents,
                    }
                }
            )
            actual = ls_session.text_document_formatting(
                {
                    "textDocument": {"uri": uri},
                    "options": {"tabSize": 4, "insertSpaces": True},
                }
            )

    expected = [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": len(lines), "character": 0},
            },
            "newText": formatted_test_file_path.read_text("utf-8"),
        }
    ]
    diff = difflib.unified_diff(
        expected[0]["newText"].splitlines(),
        actual[0]["newText"].splitlines(),
        fromfile="expected",
        tofile="actual",
    )

    assert_that(actual, is_(expected), "\n".join(diff))


def test_formatting_with_default_config():
    """Test formatting a snakemake file with a default configuration file in the workspace."""
    formatted_test_file_path = constants.TEST_DATA / "sample3" / "formatted.smk"
    unformatted_test_file_path = constants.TEST_DATA / "sample3" / "toFormat.smk"

    contents = unformatted_test_file_path.read_text("utf-8")
    lines = contents.splitlines(keepends=False)

    actual = []
    with utils.SnakemakeFile(contents, unformatted_test_file_path.parent) as file:
        uri = utils.as_uri(file.fullpath)

        with session.LspSession() as ls_session:
            ls_session.initialize()
            ls_session.notify_did_open(
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "snakemake",
                        "version": 1,
                        "text": contents,
                    }
                }
            )
            actual = ls_session.text_document_formatting(
                {
                    "textDocument": {"uri": uri},
                    "options": {"tabSize": 4, "insertSpaces": True},
                }
            )

    expected = [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": len(lines), "character": 0},
            },
            "newText": formatted_test_file_path.read_text("utf-8"),
        }
    ]

    diff = difflib.unified_diff(
        expected[0]["newText"].splitlines(),
        actual[0]["newText"].splitlines(),
        fromfile="expected",
        tofile="actual",
    )

    assert_that(actual, is_(expected), "\n".join(diff))
