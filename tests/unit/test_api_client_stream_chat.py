import sys
import types

if "requests" not in sys.modules:
    sys.modules["requests"] = types.SimpleNamespace(get=lambda *args, **kwargs: None)

import json

from seq_llm.core.api_client import APIClient


class FakeResponse:
    def __init__(self, lines):
        self._lines = lines

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def raise_for_status(self):
        return None

    def iter_lines(self):
        for line in self._lines:
            yield line


class FakeHTTPXClient:
    def __init__(self, lines):
        self._lines = lines

    def stream(self, method, path, json=None, timeout=None):
        assert method == "POST"
        assert path == "/v1/chat/completions"
        assert json is not None and json.get("stream") is True
        return FakeResponse(self._lines)

    def close(self):
        return None


def make_client(lines):
    client = APIClient(base_url="http://localhost:8000")
    client.client = FakeHTTPXClient(lines)
    return client


def test_stream_chat_parses_sse_token_chunks_and_done():
    payload_1 = json.dumps({"choices": [{"delta": {"content": "Hel"}}]})
    payload_2 = json.dumps({"choices": [{"delta": {"content": "lo"}}]})
    lines = [
        "event: message",
        "",
        f"data: {payload_1}",
        f"data: {payload_2}",
        "data: [DONE]",
        f"data: {json.dumps({'choices': [{'delta': {'content': 'ignored'}}]})}",
    ]

    client = make_client(lines)

    chunks = list(client.stream_chat(messages=[{"role": "user", "content": "Hi"}], model="local"))

    assert chunks == ["Hel", "lo"]


def test_stream_chat_ignores_role_only_chunks():
    payload_role = json.dumps({"choices": [{"delta": {"role": "assistant"}}]})
    payload_text = json.dumps({"choices": [{"delta": {"content": "answer"}}]})
    client = make_client([f"data: {payload_role}", f"data: {payload_text}", "data: [DONE]"])

    chunks = list(client.stream_chat(messages=[{"role": "user", "content": "Hi"}], model="local"))

    assert chunks == ["answer"]


def test_stream_chat_handles_malformed_json_and_fallback_fields():
    payload_text_fallback = json.dumps({"choices": [{"text": "fallback-a"}]})
    payload_message_fallback = json.dumps(
        {"choices": [{"message": {"role": "assistant", "content": "fallback-b"}}]}
    )
    client = make_client(
        [
            "data: {not-json}",
            f"data: {payload_text_fallback}",
            f"data: {payload_message_fallback}",
            "data: [DONE]",
        ]
    )

    chunks = list(client.stream_chat(messages=[{"role": "user", "content": "Hi"}], model="local"))

    assert chunks == ["fallback-a", "fallback-b"]
