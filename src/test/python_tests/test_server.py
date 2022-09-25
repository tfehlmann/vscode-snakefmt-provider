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

LINTING_FILE_EXPECTED = {
    constants.TEST_DATA
    / "sample1"
    / "toFormat.smk": {
        "diagnostics": [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 0},
                },
                "message": "Document is not following snakefmt formatting",
                "severity": 3,
                "code": "snakefmt:not-formatted",
                "source": SERVER_INFO["name"],
            },
        ],
    },
    constants.TEST_DATA
    / "linting"
    / "test1.smk": {
        "diagnostics": [
            {
                "range": {
                    "start": {"line": 10, "character": 0},
                    "end": {"line": 10, "character": 14},
                },
                "message": 'InvalidPython: Black error:\nCannot parse: 11:0: test = "test"',
                "severity": 1,
                "code": "snakefmt:black-error:invalid-python",
                "source": SERVER_INFO["name"],
            },
        ],
    },
    constants.TEST_DATA
    / "linting"
    / "test2.smk": {
        "diagnostics": [
            {
                "range": {
                    "start": {"line": 13, "character": 0},
                    "end": {"line": 13, "character": 9},
                },
                "message": "InvalidPython: Black error:\nCannot parse: 14:4: rue all:",
                "severity": 1,
                "code": "snakefmt:black-error:invalid-python",
                "source": SERVER_INFO["name"],
            },
        ],
    },
    constants.TEST_DATA
    / "linting"
    / "test3.smk": {
        "diagnostics": [
            {
                "range": {
                    "start": {"line": 21, "character": 8},
                    "end": {"line": 22, "character": 64},
                },
                "message": 'InvalidParameterSyntax: 22"data/genome.fa"\n'
                'lambda wildcards: config["samples2"][wildcards.sample]',
                "severity": 1,
                "code": "snakefmt:invalid-parameter-syntax",
                "source": SERVER_INFO["name"],
            },
        ],
    },
    constants.TEST_DATA
    / "linting"
    / "test4.smk": {
        "diagnostics": [
            {
                "range": {
                    "start": {"line": 22, "character": 4},
                    "end": {"line": 22, "character": 11},
                },
                "message": "SyntaxError: L23: Unrecognised keyword 'outut' in rule definition",
                "severity": 1,
                "code": "snakefmt:syntax-error",
                "source": SERVER_INFO["name"],
            },
        ],
    },
    constants.TEST_DATA
    / "linting"
    / "test5.smk": {
        "diagnostics": [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 0},
                },
                "message": "An unexpected error occurred, Snakefmt could not format this document.",
                "severity": 2,
                "code": "snakefmt:unexpected-error",
                "source": SERVER_INFO["name"],
            },
        ],
    },
    constants.TEST_DATA
    / "linting"
    / "test6.smk": {
        "diagnostics": [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 0},
                },
                "message": "An unexpected error occurred, Snakefmt could not format this document.",
                "severity": 2,
                "code": "snakefmt:unexpected-error",
                "source": SERVER_INFO["name"],
            },
        ],
    },
}


def lint_file(test_file_path):
    """Lint a file and return the diagnostics."""
    test_file_uri = utils.as_uri(str(test_file_path))
    contents = test_file_path.read_text()

    actual = {}

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

    return actual


def test_linting():
    """Test linting on file open."""
    for file_path, expected in LINTING_FILE_EXPECTED.items():
        actual = lint_file(file_path)
        for actual_diag, expected_diag in zip(
            actual["diagnostics"], expected["diagnostics"]
        ):
            assert actual_diag == expected_diag


def test_formatting():
    """Test formatting a snakemake file."""
    formatted_test_file_path = constants.TEST_DATA / "sample1" / "formatted.smk"
    unformatted_test_file_path = constants.TEST_DATA / "sample1" / "toFormat.smk"

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


def test_formatting_with_custom_config():
    """Test formatting a snakemake file and providing a custom config file."""
    formatted_test_file_path = constants.TEST_DATA / "sample2" / "formatted.smk"
    unformatted_test_file_path = constants.TEST_DATA / "sample2" / "toFormat.smk"
    config_file = constants.TEST_DATA / "sample2" / "config.toml"

    contents = unformatted_test_file_path.read_text("utf-8")
    lines = contents.splitlines(keepends=False)

    actual = []
    with utils.SnakemakeFile(contents, unformatted_test_file_path.parent) as file:
        uri = utils.as_uri(file.fullpath)

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
