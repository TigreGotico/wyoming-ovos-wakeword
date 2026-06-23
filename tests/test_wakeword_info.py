"""Tests for the wake word Info response.

Validates that the Info structure contains correct WakeProgram/WakeModel
entries based on mycroft.conf hotwords.
"""

from asyncio import StreamReader, StreamWriter
from unittest.mock import MagicMock, patch

import pytest
from wyoming.event import Event
from wyoming.info import Info

from wyoming_ovos_wakeword.__main__ import OVOSWakeWordEventHandler


def _streams():
    return MagicMock(spec=StreamReader), MagicMock(spec=StreamWriter)


@pytest.mark.asyncio
async def test_info_contains_all_hotwords():
    """Info response includes every hotword from configuration."""
    reader, writer = _streams()

    class MockArgs:
        pass

    fake_hotwords = {
        "hey_mycroft": {"module": "ovos-ww-plugin-precise-lite", "lang": "en"},
        "wake_up": {"module": "ovos-ww-plugin-vosk", "lang": "en"},
    }

    with patch(
        "wyoming_ovos_wakeword.__main__.Configuration"
    ) as mock_cfg:
        mock_cfg.return_value.get.side_effect = lambda key, default=None: {
            "listener": {"wake_word": "hey_mycroft"},
            "hotwords": fake_hotwords,
        }.get(key, default)

        handler = OVOSWakeWordEventHandler(MockArgs(), reader=reader, writer=writer)
        info = handler._get_info()

        assert len(info.wake) == 1
        program = info.wake[0]
        assert program.name == "ovos-wakeword-plugins"
        assert program.installed is True

        model_names = {m.name for m in program.models}
        assert "hey_mycroft" in model_names
        assert "wake_up" in model_names


@pytest.mark.asyncio
async def test_info_empty_hotwords():
    """Info works with no hotwords configured."""
    reader, writer = _streams()

    class MockArgs:
        pass

    with patch(
        "wyoming_ovos_wakeword.__main__.Configuration"
    ) as mock_cfg:
        mock_cfg.return_value.get.side_effect = lambda key, default=None: {
            "listener": {"wake_word": "hey_mycroft"},
            "hotwords": {},
        }.get(key, default)

        handler = OVOSWakeWordEventHandler(MockArgs(), reader=reader, writer=writer)
        info = handler._get_info()

        assert len(info.wake) == 1
        assert len(info.wake[0].models) == 0
