# tests/test_hardware_detector.py
from seq_llm.hardware.detector import detect_hardware


def test_detect_hardware_profile():
    profile = detect_hardware()

    assert profile.cpu_logical >= 1
    assert profile.cpu_physical >= 1
    assert profile.total_ram_gb > 0
    assert isinstance(profile.has_gpu, bool)
    assert isinstance(profile.cuda_available, bool)


def test_hardware_profile_to_dict_serializes_probe_raw():
    profile = detect_hardware()
    profile_dict = profile.to_dict()

    assert "probe_raw" in profile_dict
    assert isinstance(profile_dict["probe_raw"], str)
