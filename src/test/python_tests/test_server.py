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
    TEST_FILE_PATH = constants.TEST_DATA / "sample1" / "toFormat.smk"
    TEST_FILE_URI = utils.as_uri(str(TEST_FILE_PATH))
    contents = TEST_FILE_PATH.read_text()

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
                    "uri": TEST_FILE_URI,
                    "languageId": "snakemake",
                    "version": 1,
                    "text": contents,
                }
            }
        )

        # wait for some time to receive all notifications
        done.wait(TIMEOUT)

    expected = {
        "uri": TEST_FILE_URI,
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
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample1" / "formatted.smk"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample1" / "toFormat.smk"

    contents = UNFORMATTED_TEST_FILE_PATH.read_text()
    lines = contents.splitlines(keepends=False)

    actual = []
    with utils.SnakemakeFile(contents, UNFORMATTED_TEST_FILE_PATH.parent) as f:
        uri = utils.as_uri(str(f))

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
            "newText": FORMATTED_TEST_FILE_PATH.read_text(),
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
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample2" / "formatted.smk"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample2" / "toFormat.smk"
    CONFIG_FILE = constants.TEST_DATA / "sample2" / "config.toml"

    contents = UNFORMATTED_TEST_FILE_PATH.read_text()
    lines = contents.splitlines(keepends=False)

    actual = []
    with utils.SnakemakeFile(contents, UNFORMATTED_TEST_FILE_PATH.parent) as f:
        uri = utils.as_uri(str(f))

        with session.LspSession() as ls_session:
            init_options = defaults.VSCODE_DEFAULT_INITIALIZE["initializationOptions"]
            init_options["settings"][0]["args"] = [
                "--config",
                str(CONFIG_FILE),
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
            "newText": FORMATTED_TEST_FILE_PATH.read_text(),
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
    FORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample3" / "formatted.smk"
    UNFORMATTED_TEST_FILE_PATH = constants.TEST_DATA / "sample3" / "toFormat.smk"

    contents = UNFORMATTED_TEST_FILE_PATH.read_text()
    lines = contents.splitlines(keepends=False)

    actual = []
    with utils.SnakemakeFile(contents, UNFORMATTED_TEST_FILE_PATH.parent) as f:
        uri = utils.as_uri(f.fullpath)

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
            "newText": FORMATTED_TEST_FILE_PATH.read_text(),
        }
    ]

    diff = difflib.unified_diff(
        expected[0]["newText"].splitlines(),
        actual[0]["newText"].splitlines(),
        fromfile="expected",
        tofile="actual",
    )

    assert_that(actual, is_(expected), "\n".join(diff))