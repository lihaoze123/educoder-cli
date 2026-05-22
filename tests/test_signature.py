from educoder_cli import signature


def test_gen_signature_returns_timestamp_and_signature(monkeypatch) -> None:
    monkeypatch.setattr(signature.time, "time", lambda: 1234.567)

    timestamp, value = signature.gen_signature("get")

    assert timestamp == 1234567
    assert len(value) == 32
    int(value, 16)


def test_gen_signature_normalizes_method_case(monkeypatch) -> None:
    monkeypatch.setattr(signature.time, "time", lambda: 1234.567)

    assert signature.gen_signature("get") == signature.gen_signature("GET")
