import flet as ft

from app.ui.challenges_utils import (
    color,
    friendly_date,
    group_rewards_by_challenge,
    http_error_detail,
    loading_placeholder,
    normalize_api_list,
    status_theme,
)


class _DummyResponse:
    def __init__(self, status_code=500, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


class _DummyHTTPError(Exception):
    def __init__(self, response):
        super().__init__("dummy error")
        self.response = response


def test_group_rewards_by_challenge_groups_ids():
    rewards = [
        {"chall_id": 1, "reward_id": 10},
        {"chall_id": 1, "reward_id": 11},
        {"chall_id": 2, "reward_id": 20},
    ]
    grouped = group_rewards_by_challenge(rewards)
    assert set(grouped.keys()) == {1, 2}
    assert len(grouped[1]) == 2


def test_group_rewards_by_challenge_skips_invalid_records():
    rewards = [
        {"chall_id": 3, "reward_id": 30},
        {"reward_id": 31},
        "bad",
        None,
    ]
    grouped = group_rewards_by_challenge(rewards)
    assert grouped == {3: [{"chall_id": 3, "reward_id": 30}]}


def test_normalize_api_list_from_dict_key():
    payload = {"results": [{"a": 1}, {"b": 2}]}
    assert normalize_api_list(payload) == [{"a": 1}, {"b": 2}]


def test_normalize_api_list_falls_back_to_any_list_value():
    payload = {"meta": 1, "other": [{"a": 1}, "skip", {"b": 2}]}
    assert normalize_api_list(payload, keys=["missing"]) == [{"a": 1}, {"b": 2}]


def test_normalize_api_list_from_list_input():
    payload = [{"a": 1}, "skip", {"b": 2}]
    assert normalize_api_list(payload) == [{"a": 1}, {"b": 2}]


def test_normalize_api_list_returns_empty_for_non_collection_payload():
    assert normalize_api_list("not-a-collection") == []


def test_normalize_api_list_prefers_first_matching_key_order():
    payload = {
        "data": [{"from": "data"}],
        "results": [{"from": "results"}],
    }
    assert normalize_api_list(payload, keys=["results", "data"]) == [{"from": "results"}]


def test_friendly_date_formats_iso_date():
    assert friendly_date("2026-05-11") == "11 May 2026"


def test_friendly_date_fallback_for_invalid_date():
    assert friendly_date("not-a-date") == "not-a-date"


def test_friendly_date_unknown_for_empty_value():
    assert friendly_date(None) == "unknown"


def test_http_error_detail_uses_response_detail():
    err = _DummyHTTPError(_DummyResponse(400, {"detail": "bad request"}))
    assert http_error_detail(err) == "bad request"


def test_http_error_detail_falls_back_to_exception_text_when_detail_missing():
    err = _DummyHTTPError(_DummyResponse(400, {"message": "no detail key"}))
    assert http_error_detail(err) == "dummy error"


def test_http_error_detail_fallback_to_status_code():
    class _BrokenResponse(_DummyResponse):
        def json(self):
            raise ValueError("bad json")

    err = _DummyHTTPError(_BrokenResponse(503, {}))
    assert "server error 503" in http_error_detail(err)


def test_status_theme_badges():
    assert status_theme("active")["badge"] == "active"
    assert status_theme("completed")["badge"] == "completed"
    assert status_theme("failed")["badge"] == "failed"


def test_status_theme_defaults_to_active_for_unknown_status():
    assert status_theme("something-else")["badge"] == "active"


def test_color_returns_fallback_for_missing_color_name():
    fallback = "fallback-color"
    assert color("THIS_COLOR_DOES_NOT_EXIST", fallback) == fallback


def test_loading_placeholder_builds_row_with_spinner_and_label():
    row = loading_placeholder("loading challenges")
    assert isinstance(row, ft.Row)
    assert len(row.controls) == 2
    assert isinstance(row.controls[0], ft.ProgressRing)
    assert isinstance(row.controls[1], ft.Text)
    assert row.controls[1].value == "loading challenges"
