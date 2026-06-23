#!/usr/bin/env python3
import argparse
import asyncio
import logging
import signal
import time
from functools import partial
from pathlib import Path
from typing import Dict, Optional

from ovos_config import Configuration
from ovos_plugin_manager.templates.hotwords import HotWordEngine
from ovos_plugin_manager.wakewords import OVOSWakeWordFactory
from wyoming.audio import AudioChunk, AudioChunkConverter, AudioStart, AudioStop
from wyoming.error import Error
from wyoming.event import Event
from wyoming.info import Attribution, Describe, Info, WakeModel, WakeProgram
from wyoming.server import AsyncEventHandler, AsyncServer, AsyncTcpServer
from wyoming.wake import Detect, Detection, NotDetected

from wyoming_ovos_wakeword.version import __version__

_LOGGER = logging.getLogger()
_DIR = Path(__file__).parent


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default="stdio://",
                        help="unix:// or tcp:// (default: stdio://)")
    parser.add_argument(
        "--zeroconf",
        nargs="?",
        const="ovos-ww-plugin",
        help="Enable discovery over zeroconf with optional name (default: ovos-ww-plugin)",
    )
    parser.add_argument("--debug", action="store_true", help="Log DEBUG messages")
    parser.add_argument(
        "--log-format", default=logging.BASIC_FORMAT,
        help="Format for log messages",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="Print version and exit",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format=args.log_format,
    )
    _LOGGER.debug(args)

    _LOGGER.info("Ready")

    server = AsyncServer.from_uri(args.uri)

    if args.zeroconf:
        if not isinstance(server, AsyncTcpServer):
            raise ValueError("Zeroconf requires tcp:// uri")
        tcp_server: AsyncTcpServer = server
        from wyoming.zeroconf import HomeAssistantZeroconf
        await HomeAssistantZeroconf(
            name=args.zeroconf,
            port=tcp_server.port,
            host=tcp_server.host,
        ).register_server()
        _LOGGER.debug("Zeroconf discovery enabled")

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(server.stop()))

    try:
        await server.run(partial(OVOSWakeWordEventHandler, args))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass


# -----------------------------------------------------------------------------


class OVOSWakeWordEventHandler(AsyncEventHandler):
    """Wyoming event handler for wake word detection.

    Loads OVOS hotword engines on demand and feeds them audio chunks
    from the client. Sends ``Detection`` on match, ``NotDetected``
    when the audio stream ends without a match.
    """

    def __init__(
            self,
            cli_args: argparse.Namespace,
            *args,
            **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.cli_args = cli_args
        self.client_id = str(time.monotonic_ns())
        self.converter = AudioChunkConverter(rate=16000, width=2, channels=1)
        self.default_ww = Configuration().get("listener", {}).get(
            "wake_word", "hey_mycroft"
        )
        self.models: Dict[str, HotWordEngine] = {}
        self.active_detectors = [self.default_ww]
        self._detection: bool = False

        _LOGGER.debug("Client connected: %s", self.client_id)

    async def load_wakewords(self, names):
        """Ensure all named wake-word engines are loaded."""
        ww_definitions = Configuration().get("hotwords", {})
        for ww_name in names:
            if ww_name in self.models:
                continue
            if ww_name not in ww_definitions:
                raise ValueError(f"Unknown hotword {ww_name}")
            self.models[ww_name] = OVOSWakeWordFactory.create_hotword(
                ww_name, ww_definitions[ww_name]
            )
            _LOGGER.debug("Loaded model: %s", ww_name)

    async def handle_event(self, event: Event) -> bool:
        try:
            if Describe.is_type(event.type):
                wyoming_info = self._get_info()
                await self.write_event(wyoming_info.event())
                _LOGGER.debug("Sent info to client: %s", self.client_id)
                return True

            if Detect.is_type(event.type):
                detect = Detect.from_event(event)
                if detect.names:
                    self.active_detectors = detect.names
                    await self.load_wakewords(detect.names)
                return True

            if AudioStart.is_type(event.type):
                self._detection = False
                self.active_detectors = self.active_detectors or [self.default_ww]
                await self.load_wakewords(self.active_detectors)
                for name in self.active_detectors:
                    self.models[name].reset()

            elif AudioChunk.is_type(event.type):
                chunk = self.converter.convert(AudioChunk.from_event(event))
                for wake_word in self.active_detectors:
                    detector = self.models[wake_word]
                    detector.update(chunk.audio)
                    if detector.found_wake_word(None):
                        _LOGGER.debug(
                            "Detected %s from client %s",
                            wake_word,
                            self.client_id,
                        )
                        await self.write_event(
                            Detection(
                                name=wake_word,
                                timestamp=chunk.timestamp,
                            ).event()
                        )
                        self._detection = True

            elif AudioStop.is_type(event.type):
                if not self._detection:
                    await self.write_event(NotDetected().event())
                    _LOGGER.debug(
                        "Audio stopped without detection from client: %s",
                        self.client_id,
                    )
            else:
                _LOGGER.debug(
                    "Unexpected event: type=%s, data=%s", event.type, event.data
                )

            return True

        except Exception as err:
            _LOGGER.exception("Wake word handler error")
            await self.write_event(
                Error(text=str(err), code=err.__class__.__name__).event()
            )
            return False

    async def disconnect(self) -> None:
        _LOGGER.debug("Client disconnected: %s", self.client_id)

    def _get_info(self) -> Info:
        return Info(
            wake=[
                WakeProgram(
                    name="ovos-wakeword-plugins",
                    description="Wake word detection via OpenVoiceOS plugins",
                    attribution=Attribution(
                        name="OpenVoiceOS",
                        url="https://github.com/OpenVoiceOS/ovos-plugin-manager",
                    ),
                    installed=True,
                    version=__version__,
                    models=[
                        WakeModel(
                            name=ww_name,
                            description=f"wake-word via {ww_cfg.get('module', '?')}",
                            phrase=ww_name.replace("_", " ").title(),
                            attribution=Attribution(
                                name="OpenVoiceOS",
                                url="https://github.com/OpenVoiceOS/ovos-plugin-manager",
                            ),
                            installed=True,
                            languages=[
                                ww_cfg.get("lang", Configuration().get("lang", "en"))
                            ],
                            version=__version__,
                        )
                        for ww_name, ww_cfg in Configuration()
                        .get("hotwords", {})
                        .items()
                    ],
                )
            ],
        )


# -----------------------------------------------------------------------------


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
