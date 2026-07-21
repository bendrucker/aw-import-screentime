from pathlib import Path

import pytest

import aw_import_screentime.__main__ as mod


@pytest.fixture
def streams_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    streams = tmp_path / "streams"
    streams.mkdir()
    for name in ("device-b", "device-a"):
        (streams / name).mkdir()
    (streams / "stray-file").write_text("")
    monkeypatch.setattr(mod, "STREAMS_DIR", streams)
    return streams


def test_get_stream_device_ids_lists_directories_sorted(streams_dir: Path) -> None:
    assert mod.get_stream_device_ids() == ["device-a", "device-b"]


def test_get_stream_device_ids_missing_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mod, "STREAMS_DIR", tmp_path / "absent")

    assert mod.get_stream_device_ids() == []


def test_resolve_target_devices_prefers_explicit_selection(
    streams_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicitly named device is honored even when DevicePeer omits it.

    DevicePeer files some devices under a platform value that does not match the
    device and misses other synced peers entirely, so intersecting the two would
    silently drop the requested device.
    """
    monkeypatch.setattr(mod, "get_device_ids", lambda *_args, **_kwargs: ["device-a"])

    assert mod.resolve_target_devices(["unlisted-device"]) == ["unlisted-device"]


def test_resolve_target_devices_all_devices_uses_streams(
    streams_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mod, "get_device_ids", lambda *_args, **_kwargs: ["device-a"])

    assert mod.resolve_target_devices(None, all_devices=True) == [
        "device-a",
        "device-b",
    ]


def test_resolve_target_devices_defaults_to_device_peer(
    streams_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[int] = []

    def fake_get_device_ids(_db_path: Path, platform: int = 2) -> list[str]:
        seen.append(platform)
        return ["from-device-peer"]

    monkeypatch.setattr(mod, "get_device_ids", fake_get_device_ids)

    assert mod.resolve_target_devices(None, platform=7) == ["from-device-peer"]
    assert seen == [7]


@pytest.mark.parametrize(
    ("cli_flag", "config_flag", "expected"),
    [
        (False, None, False),
        (False, False, False),
        (False, True, True),
        (True, None, True),
        (True, False, True),
    ],
)
def test_resolve_all_devices_flag(
    cli_flag: bool, config_flag: bool | None, expected: bool
) -> None:
    assert mod.resolve_all_devices_flag(cli_flag, config_flag) is expected
