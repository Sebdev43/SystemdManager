"""Tests for service JSON persistence: round-trip, migration, error handling.

Dependency-free (no GUI/questionary imports) so they run in any environment.
"""

import json

import pytest

from src.models.service_model import ServiceModel


def test_to_json_uses_lowercase_section_keys():
    data = ServiceModel("svc").to_json()
    assert {"name", "unit", "service", "install"} <= set(data.keys())
    # The GUI reads these exact lowercase keys; capitalized must never appear.
    assert "Unit" not in data
    assert "Service" not in data
    assert "Install" not in data


def test_load_from_json_missing_section_uses_defaults(tmp_path):
    path = tmp_path / "partial.json"
    path.write_text(json.dumps({"name": "partial", "service": {"type": "simple"}}))
    service = ServiceModel.load_from_json(str(path))
    # Missing unit/install sections load defaults rather than raising KeyError.
    assert service.name == "partial"
    assert service.service.type == "simple"
    assert service.unit.description == ""
    assert service.install.wanted_by is None


def test_load_from_json_prefers_data_name_over_filename(tmp_path):
    path = tmp_path / "renamed-on-disk.json"
    path.write_text(json.dumps({"name": "real-service", "service": {}}))
    service = ServiceModel.load_from_json(str(path))
    assert service.name == "real-service"


def test_load_from_json_falls_back_to_filename_when_no_name(tmp_path):
    path = tmp_path / "from-file.json"
    path.write_text(json.dumps({"service": {"type": "simple"}}))
    service = ServiceModel.load_from_json(str(path))
    assert service.name == "from-file"


def test_load_from_json_invalid_json_raises_valueerror(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not valid json")
    with pytest.raises(ValueError):
        ServiceModel.load_from_json(str(path))


def test_load_from_json_migrates_start_limit_to_unit(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps(
            {
                "name": "legacy",
                "service": {
                    "type": "simple",
                    "start_limit_interval": 300,
                    "start_limit_burst": 7,
                },
            }
        )
    )
    service = ServiceModel.load_from_json(str(path))
    assert service.unit.start_limit_interval == 300
    assert service.unit.start_limit_burst == 7
    assert not hasattr(service.service, "start_limit_interval")
    assert not hasattr(service.service, "start_limit_burst")


def test_save_to_json_bare_filename_does_not_crash(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ServiceModel("bare").save_to_json("bare.json")  # no directory component
    assert (tmp_path / "bare.json").exists()


def test_save_load_round_trip_preserves_fields(tmp_path):
    service = ServiceModel("round")
    service.unit.description = "Round trip"
    service.service.working_directory = "/opt/app"
    service.service.exec_start = "/usr/bin/python3 app.py"
    service.service.user = "appuser"
    service.install.wanted_by = ["multi-user.target"]
    path = tmp_path / "round.json"
    service.save_to_json(str(path))
    loaded = ServiceModel.load_from_json(str(path))
    assert loaded.name == "round"
    assert loaded.unit.description == "Round trip"
    assert loaded.service.exec_start == "/usr/bin/python3 app.py"
    assert loaded.service.user == "appuser"
    assert loaded.install.wanted_by == ["multi-user.target"]


# --- security hardening tests (adversarial review fixes) -------------------


@pytest.mark.parametrize(
    "bad_name",
    [
        "../../etc/cron.d/pwn",
        "foo; rm -rf x",
        "a/b",
        "foo bar",
        "$(touch x)",
        "name\nInjected=1",
    ],
)
def test_load_from_json_rejects_dangerous_name(tmp_path, bad_name):
    # A crafted name must not flow into systemd paths / systemctl commands.
    path = tmp_path / "svc.json"
    path.write_text(json.dumps({"name": bad_name, "service": {}}))
    with pytest.raises(ValueError):
        ServiceModel.load_from_json(str(path))


def test_load_from_json_non_string_name_falls_back_to_filename(tmp_path):
    path = tmp_path / "good.json"
    path.write_text(json.dumps({"name": 123, "service": {"type": "simple"}}))
    service = ServiceModel.load_from_json(str(path))
    assert service.name == "good"


def test_load_from_json_invalid_utf8_raises_valueerror(tmp_path):
    path = tmp_path / "binary.json"
    path.write_bytes(b"\xff\xfe not valid utf-8")
    with pytest.raises(ValueError):
        ServiceModel.load_from_json(str(path))
