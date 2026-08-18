"""Pytest path bootstrap and network-forbidden fixture."""

from __future__ import annotations

import socket

import httpx
import pytest

from eval_lab.runner import OpenRouterClient


class NetworkForbidden(RuntimeError):
    pass


def _block(*_args, **_kwargs):
    raise NetworkForbidden("network I/O is forbidden in the free oracle lab")


@pytest.fixture
def network_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(socket, "socket", _block)
    monkeypatch.setattr(socket, "create_connection", _block)
    monkeypatch.setattr(httpx, "Client", _block)
    monkeypatch.setattr(httpx, "AsyncClient", _block)
    monkeypatch.setattr(httpx, "request", _block)
    monkeypatch.setattr(OpenRouterClient, "complete", _block)
    monkeypatch.setattr(OpenRouterClient, "__init__", lambda self, *args, **kwargs: (_block()))
