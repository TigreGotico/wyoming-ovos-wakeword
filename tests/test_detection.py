"""Tests for wake word detection flow with mock engines."""

from asyncio import StreamReader, StreamWriter
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.event import Event
from wyoming.wake import Detect, Detection, NotDetected

from wyoming_ovos_wakeword.__main__ import OVOSWakeWordEventHandler


def _streams():
    return MagicMock(spec=StreamReader), MagicMock(spec=StreamWriter)


def _handler(hotwords=None):
    reader, writer = _streams()
    if hotwords is None:
        hotwords = {
            "hey_mycroft": {"module": "test_plugin", "sensitivity": 0.5}
        }

    class MockArgs:
        pass

    with patch(
        "wyoming_ovos_wakeword.__main__.Configuration"
    ) as mock_cfg:
        mock_cfg.return_value.get.side_effect = lambda key, default=None: {
            "listener": {"wake_word": "hey_mycroft"},
            "hotwords": hotwords,
        }.get(key, default)

        return OVOSWakeWordEventHandler(MockArgs(), reader=reader, writer=writer)


@pytest.mark.asyncio
async def test_detection_sends_detection_event():
    """Detection triggers a Detection event."""
    handler = _handler()
    mock_engine = MagicMock()
    mock_engine.found_wake_word.return_value = True
    handler.models = {"hey_mycroft": mock_engine}
    handler.active_detectors = ["hey_mycroft"]

    captured = []

    async def capture(event):
        captured.append(event)

    handler.write_event = capture

    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=b"\x00\x00" * 160)
    await handler.handle_event(chunk.event())

    detection_events = [e for e in captured if e.type == "detection"]
    assert len(detection_events) == 1
    d = Detection.from_event(detection_events[0])
    assert d.name == "hey_mycroft"


@pytest.mark.asyncio
async def test_detection_sets_flag():
    """Detection sets _detection flag, suppressing NotDetected."""
    handler = _handler()
    mock_engine = MagicMock()
    mock_engine.found_wake_word.return_value = True
    handler.models = {"hey_mycroft": mock_engine}
    handler.active_detectors = ["hey_mycroft"]

    captured = []

    async def capture(event):
        captured.append(event)

    handler.write_event = capture

    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=b"\x00\x00" * 160)
    await handler.handle_event(chunk.event())
    assert handler._detection is True

    await handler.handle_event(AudioStop().event())
    not_detected = [e for e in captured if e.type == "not-detected"]
    assert len(not_detected) == 0


@pytest.mark.asyncio
async def test_no_detection_sends_not_detected():
    """No detection on AudioStop sends NotDetected."""
    handler = _handler()
    mock_engine = MagicMock()
    mock_engine.found_wake_word.return_value = False
    handler.models = {"hey_mycroft": mock_engine}
    handler.active_detectors = ["hey_mycroft"]

    captured = []

    async def capture(event):
        captured.append(event)

    handler.write_event = capture

    await handler.handle_event(AudioStop().event())
    not_detected = [e for e in captured if e.type == "not-detected"]
    assert len(not_detected) == 1


@pytest.mark.asyncio
async def test_multiple_detectors():
    """Multiple active detectors are checked on each chunk."""
    handler = _handler()
    engine_a = MagicMock()
    engine_a.found_wake_word.return_value = False
    engine_b = MagicMock()
    engine_b.found_wake_word.return_value = True
    handler.models = {"ww_a": engine_a, "ww_b": engine_b}
    handler.active_detectors = ["ww_a", "ww_b"]

    captured = []

    async def capture(event):
        captured.append(event)

    handler.write_event = capture

    await handler.handle_event(
        AudioChunk(rate=16000, width=2, channels=1, audio=b"\x00\x00" * 160).event()
    )

    engine_a.update.assert_called_once()
    engine_b.update.assert_called_once()
    detection_events = [e for e in captured if e.type == "detection"]
    assert len(detection_events) == 1
    assert Detection.from_event(detection_events[0]).name == "ww_b"


@pytest.mark.asyncio
async def test_unknown_hotword_raises():
    """load_wakewords raises ValueError for unknown hotword."""
    handler = _handler()
    with pytest.raises(ValueError, match="Unknown hotword"):
        await handler.load_wakewords(["nonexistent"])


@pytest.mark.asyncio
async def test_audio_start_resets_and_loads():
    """AudioStart resets detection state and loads models."""
    handler = _handler()
    handler.active_detectors = []
    mock_engine = MagicMock()
    handler.models = {"hey_mycroft": mock_engine}
    with patch.object(handler, "load_wakewords") as mock_load:
        result = await handler.handle_event(
            AudioStart(rate=16000, width=2, channels=1).event()
        )
        assert result is True
        assert handler._detection is False
        mock_load.assert_called_once()
        mock_engine.reset.assert_called_once()
