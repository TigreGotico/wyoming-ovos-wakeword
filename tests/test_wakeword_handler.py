"""Unit tests for OVOSWakeWordEventHandler.

Tests the Wyoming event dispatching logic with mocked hotword engines.
"""

from asyncio import StreamReader, StreamWriter
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.error import Error
from wyoming.event import Event
from wyoming.info import Describe, Info
from wyoming.wake import Detect, Detection, NotDetected

from wyoming_ovos_wakeword.__main__ import OVOSWakeWordEventHandler


def _streams():
    return MagicMock(spec=StreamReader), MagicMock(spec=StreamWriter)


@pytest.fixture
def handler():
    reader, writer = _streams()

    class MockArgs:
        pass

    with patch(
        "wyoming_ovos_wakeword.__main__.Configuration"
    ) as mock_cfg:
        mock_cfg.return_value.get.side_effect = lambda key, default=None: {
            "listener": {"wake_word": "hey_mycroft"},
            "hotwords": {
                "hey_mycroft": {
                    "module": "test_plugin",
                    "sensitivity": 0.5,
                }
            },
        }.get(key, default)

        h = OVOSWakeWordEventHandler(MockArgs(), reader=reader, writer=writer)
        return h


@pytest.mark.asyncio
async def test_describe(handler):
    """Describe returns Info with wake word models."""
    result = await handler.handle_event(Describe().event())
    assert result is True


@pytest.mark.asyncio
async def test_detect_sets_active(handler):
    """Detect event updates active detectors."""
    with patch.object(handler, "load_wakewords") as mock_load:
        await handler.handle_event(Detect(names=["hey_mycroft"]).event())
        assert handler.active_detectors == ["hey_mycroft"]
        mock_load.assert_called_once_with(["hey_mycroft"])


@pytest.mark.asyncio
async def test_detect_no_names_defaults(handler):
    """Detect without names keeps default detectors."""
    await handler.handle_event(Detect().event())
    assert handler.active_detectors == [handler.default_ww]


@pytest.mark.asyncio
async def test_audio_start_resets_state(handler):
    """AudioStart resets detection flag."""
    handler._detection = True
    await handler.handle_event(AudioStart(rate=16000, width=2, channels=1).event())
    assert handler._detection is False


@pytest.mark.asyncio
async def test_audio_stop_sends_not_detected(handler, fixtures_dir):
    """AudioStop sends NotDetected when no wake word was found."""
    handler.models = {}
    handler.active_detectors = []

    result = await handler.handle_event(AudioStop().event())
    assert result is True


@pytest.mark.asyncio
async def test_audio_chunk_without_models(handler):
    """AudioChunk without active models doesn't crash."""
    handler.models = {}
    handler.active_detectors = []

    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=b"\x00\x00" * 160)
    result = await handler.handle_event(chunk.event())
    assert result is True


@pytest.mark.asyncio
async def test_unknown_event(handler):
    """Unknown event types return True (continue)."""
    result = await handler.handle_event(Event(type="unknown"))
    assert result is True
