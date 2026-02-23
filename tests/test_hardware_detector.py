# tests/test_hardware_detector.py
from seq_llm.core.auto_optimizer import suggest_params
from seq_llm.hardware.detector import detect_hardware


def test_detect_and_suggest():
    h = detect_hardware()
    assert h.total_ram_gb > 0
    params = suggest_params(h)
    assert "threads" in params and params["threads"] >= 1
    assert 0.1 <= params["max_ctx_percent"] <= 1.0
