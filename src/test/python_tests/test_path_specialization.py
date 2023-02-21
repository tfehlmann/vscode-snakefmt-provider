"""
Test for path and interpreter settings.
"""
import copy
from typing import Dict

from hamcrest import assert_that, is_

from .lsp_test_client import constants, defaults, session, utils

TEST_FILE_PATH = constants.TEST_DATA / "sample1" / "toFormat.smk"
TEST_FILE_URI = utils.as_uri(str(TEST_FILE_PATH))
TIMEOUT = 10  # 10 seconds


class CallbackObject:
    """Object that holds results for WINDOW_LOG_MESSAGE to capture argv"""

    def __init__(self):
        self.result = False

    def check_result(self):
        """returns Boolean result"""
        return self.result

    def check_for_argv_duplication(self, argv: Dict[str, str]):
        """checks if argv duplication exists and sets result boolean"""
        if argv["type"] == 4 and argv["message"].find("--from-stdin") >= 0:
            parts = argv["message"].split()
            count = len([x for x in parts if x.startswith("--from-stdin")])
            self.result = count > 1


def test_path():
    """Test linting using snakefmt bin path set."""

    init_params = copy.deepcopy(defaults.VSCODE_DEFAULT_INITIALIZE)
    init_params["initializationOptions"]["settings"][0]["path"] = ["snakefmt"]

    argv_callback_object = CallbackObject()
    contents = TEST_FILE_PATH.read_text()

    actual = True
    with session.LspSession() as ls_session:
        ls_session.set_notification_callback(
            session.WINDOW_LOG_MESSAGE,
            argv_callback_object.check_for_argv_duplication,
        )

        ls_session.initialize(init_params)
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

        # Call this second time to detect arg duplication.
        ls_session.notify_did_open(
            {
                "textDocument": {
                    "uri": TEST_FILE_URI,
                    "languageId": "snakefmt",
                    "version": 1,
                    "text": contents,
                }
            }
        )

        actual = argv_callback_object.check_result()

    assert_that(actual, is_(False))


def test_interpreter():
    """Test linting using specific python path."""
    init_params = copy.deepcopy(defaults.VSCODE_DEFAULT_INITIALIZE)
    init_params["initializationOptions"]["settings"][0]["interpreter"] = ["python"]

    argv_callback_object = CallbackObject()
    contents = TEST_FILE_PATH.read_text()

    actual = True
    with session.LspSession() as ls_session:
        ls_session.set_notification_callback(
            session.WINDOW_LOG_MESSAGE,
            argv_callback_object.check_for_argv_duplication,
        )

        ls_session.initialize(init_params)
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

        # Call this second time to detect arg duplication.
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

        actual = argv_callback_object.check_result()

    assert_that(actual, is_(False))
