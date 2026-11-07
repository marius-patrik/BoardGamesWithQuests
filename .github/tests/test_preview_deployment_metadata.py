"""Regression coverage for optional preview deployment metadata after Pages publication."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "reconcile_preview_deployments.py"
spec = importlib.util.spec_from_file_location("reconcile_preview_deployments", MODULE)
assert spec and spec.loader
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)
SHA = "a" * 40
URL = "https://example.github.io/BoardGamesWithQuests/"


class API:
    def __init__(self, *, fail: tuple[str, int] | None = None, existing: bool = False) -> None:
        self.fail = fail
        self.existing = existing
        self.calls: list[tuple[str, str, dict | None]] = []

    def get(self, path: str) -> object:
        self.calls.append(("GET", path, None))
        if self.fail and self.fail[0] == "lookup":
            raise publisher.APIError(self.fail[1], '{"message":"lookup error"}')
        if path == "pulls/422":
            return {"head": {"sha": SHA}}
        if path.startswith("deployments?environment=pr-422"):
            return [{"id": 88, "sha": SHA}] if self.existing else []
        if path.startswith("deployments?"):
            return [{"id": 77, "sha": "b" * 40, "environment": "pr-321"}]
        if path.startswith("deployments/77/statuses?"):
            return [{"state": "success"}]
        raise AssertionError(f"Unexpected GET {path}")

    def post(self, path: str, payload: dict) -> object:
        self.calls.append(("POST", path, payload))
        if self.fail and self.fail[0] in {"create", "status", "retire"}:
            operation = self.fail[0]
            if (
                (operation == "create" and path == "deployments")
                or (operation == "status" and path == "deployments/88/statuses")
                or (operation == "retire" and path == "deployments/77/statuses")
            ):
                raise publisher.APIError(
                    self.fail[1], '{"message":"metadata rejected","errors":["invalid ref"]}'
                )
        if path == "deployments":
            return {"id": 88}
        return {"state": payload["state"]}


def test_422_creation_warns_with_pr_and_api_response_then_continues(
    capsys: pytest.CaptureFixture[str],
) -> None:
    api = API(fail=("create", 422))
    publisher.reconcile(api, {"422": SHA}, URL)
    message = capsys.readouterr().out
    assert "PR #422" in message and "HTTP 422" in message
    assert "metadata rejected" in message and "invalid ref" in message
    assert not any(
        method == "POST" and path == "deployments/88/statuses" for method, path, _ in api.calls
    )
    assert any(
        method == "POST" and path == "deployments/77/statuses" for method, path, _ in api.calls
    )


def test_422_status_does_not_claim_metadata_updated(capsys: pytest.CaptureFixture[str]) -> None:
    api = API(existing=True, fail=("status", 422))
    publisher.reconcile(api, {"422": SHA}, URL)
    output = capsys.readouterr().out
    assert "PR #422" in output and "success-status update" in output
    assert "HTTP 422" in output
    assert "metadata updated" not in output


def test_422_retirement_warns_without_interrupting_reconciliation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    api = API(existing=True, fail=("retire", 422))
    publisher.reconcile(api, {"422": SHA}, URL)
    assert "PR #321" in capsys.readouterr().out


@pytest.mark.parametrize(
    "operation,status", [("create", 403), ("status", 500), ("retire", 404), ("lookup", 422)]
)
def test_other_http_errors_remain_fatal(operation: str, status: int) -> None:
    with pytest.raises(publisher.APIError) as error:
        publisher.reconcile(
            API(existing=operation != "create", fail=(operation, status)), {"422": SHA}, URL
        )
    assert error.value.status == status


def test_stale_pr_head_is_not_published() -> None:
    api = API()
    api.get = lambda path: {"head": {"sha": "b" * 40}} if path == "pulls/422" else []
    publisher.reconcile(api, {"422": SHA}, URL)
    assert not any(path == "deployments" for _, path, _ in api.calls)


@pytest.mark.parametrize("previews", [{"422": "invalid"}, {"not-a-pr": SHA}, [SHA]])
def test_invalid_preview_manifest_rejected(previews: object) -> None:
    with pytest.raises(ValueError):
        publisher.reconcile(API(), previews, URL)
