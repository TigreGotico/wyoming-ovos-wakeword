# Wyoming OVOS Wake Word Bridge

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)
[![Wyoming](https://img.shields.io/badge/wyoming-1.9+-blueviolet.svg)](https://github.com/OHF-voice/wyoming)
[![OVOS](https://img.shields.io/badge/OVOS-plugin--manager-ff69b4.svg)](https://github.com/OpenVoiceOS/ovos-plugin-manager)

Expose [OpenVoiceOS](https://openvoiceos.org) wake word (hotword) plugins as a [Wyoming protocol](https://github.com/OHF-voice/wyoming) wake service for use with Home Assistant, Rhasspy, and other Wyoming-compatible voice pipelines.

```
                         ┌──────────────────────────────────────┐
  Wyoming client         │      wyoming-ovos-wakeword            │
  (Home Assistant,       │                                      │
   Rhasspy, etc.)        │  ┌────────────────────────────────┐  │
                         │  │ OVOSWakeWordEventHandler       │  │
  Detect(names) ────────►│  │                                │  │
  AudioStart ───────────►│  │ load_wakewords(names) ─────────►│  OVOSWakeWordFactory
  AudioChunk* ──────────►│  │ HotWordEngine.update(chunk)    │  └──> Hotword plugins
                         │  │ HotWordEngine.found_wake_word()│  │
  Detection ◄────────────│  │                                │  │
  AudioStop ────────────►│  │ (if no detection)              │  │
  NotDetected ◄──────────│  │                                │  │
                         │  └────────────────────────────────┘  │
  Describe ─────────────►│  Info(wake=[WakeProgram(...)])       │
  Info ◄─────────────────│                                      │
                         └──────────────────────────────────────┘
```

## Features

- **Multiple simultaneous wake words** — Clients select which models to activate via the `Detect` event
- **Lazy model loading** — Hotword engines are loaded on demand and cached per connection
- **All configured hotwords advertised** — Every entry under `hotwords` in `mycroft.conf` is exposed in the Wyoming `Info` response
- **Zeroconf / mDNS discovery** — Optional service announcement on the local network
- **Error reporting** — Failures are sent back as Wyoming `Error` events
- **Signal handling** — Graceful shutdown on SIGINT/SIGTERM

## Installation

### From PyPI

```bash
pip install wyoming-ovos-wakeword
```

You also need to install the OVOS wake word engine(s) you intend to use, e.g.:

```bash
pip install ovos-ww-plugin-precise-lite
pip install ovos-ww-plugin-vosk
```

### From source

```bash
git clone https://github.com/OpenVoiceOS/wyoming-ovos-wakeword.git
cd wyoming-ovos-wakeword
pip install -e .
```

## Configuration

Wake word definitions are read from `mycroft.conf` under `hotwords`. The default active wake word (when no `Detect` event is received) is taken from `listener.wake_word`.

```json
{
  "listener": {
    "wake_word": "hey_mycroft"
  },
  "hotwords": {
    "hey_mycroft": {
      "module": "ovos-ww-plugin-precise-lite",
      "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/hey_mycroft.tflite",
      "expected_duration": 3,
      "trigger_level": 3,
      "sensitivity": 0.5,
      "listen": true
    },
    "hey_mycroft_vosk": {
      "module": "ovos-ww-plugin-vosk",
      "samples": ["hey mycroft"],
      "rule": "fuzzy",
      "listen": true
    },
    "wake_up": {
      "module": "ovos-ww-plugin-vosk",
      "rule": "fuzzy",
      "samples": ["wake up"],
      "lang": "en-us",
      "wakeup": true
    }
  }
}
```

All configured hotwords are advertised via `Describe`/`Info` and are selectable by name.

## Usage

```bash
# Standard TCP server with zeroconf
wyoming-ovos-wakeword --uri tcp://0.0.0.0:7893 --zeroconf

# With custom zeroconf service name
wyoming-ovos-wakeword --uri tcp://0.0.0.0:7893 --zeroconf my-ovos-ww

# Unix socket
wyoming-ovos-wakeword --uri unix:///run/wyoming-ww.sock

# Over stdio
wyoming-ovos-wakeword
```

## CLI Reference

| Argument | Required | Default | Description |
|---|---|---|---|
| `--uri` | No | `stdio://` | `tcp://HOST:PORT`, `unix:///path`, or `stdio://` |
| `--zeroconf` | No | disabled | Enable mDNS/Zeroconf discovery (optional: service name, default: `ovos-ww-plugin`) |
| `--debug` | No | `False` | Enable DEBUG-level logging |
| `--log-format` | No | `%(levelname)s:%(name)s:%(message)s` | Python log format string |
| `--version` | No | — | Print version and exit |

> Zeroconf requires a `tcp://` URI.

## Wyoming Protocol

### Wake word detection flow

```
Client → Describe
Server → Info(wake=[WakeProgram(models=[WakeModel(name="hey_mycroft", ...), ...])])

Client → Detect(names=["hey_mycroft", "wake_up"])
Client → AudioStart(rate=16000, width=2, channels=1)
       → AudioChunk (raw PCM bytes)
       → AudioChunk ...
       → Detection(name="hey_mycroft", timestamp=...)   ← on match
       → AudioChunk ...
       → AudioStop
Server → NotDetected                                  ← if no match
```

The connection stays open for continuous detection. Multiple detections can occur within a single audio stream. Audio is converted to 16 kHz / 16-bit / mono PCM automatically.

## Supported Plugin Types

Any OVOS wake word plugin implementing `HotWordEngine` from `ovos_plugin_manager.templates.hotwords`:

- `ovos-ww-plugin-precise-lite` — Mycroft Precise (TFLite)
- `ovos-ww-plugin-precise` — Mycroft Precise (full)
- `ovos-ww-plugin-vosk` — Vosk-based wake word
- `ovos-ww-plugin-pocketsphinx` — CMU PocketSphinx
- `ovos-ww-plugin-snowboy` — Snowboy (deprecated)
- `ovos-ww-plugin-openspeech` — OpenSpeech
- `ovos-ww-plugin-porcupine` — Porcupine

## Zeroconf / mDNS Discovery

When `--zeroconf` is passed, the bridge announces itself on the local network. Home Assistant and other Wyoming clients can discover the service automatically without manual IP configuration. The service is registered as `_wyoming._tcp.local.`.

## Credits

Developed by [TigreGótico](https://tigregotico.pt) for [OpenVoiceOS](https://openvoiceos.org).

[![NGI0 Commons Fund](./ngi.png)](https://nlnet.nl/project/OpenVoiceOS)

This project was funded through the [NGI0 Commons Fund](https://nlnet.nl/commonsfund),
a fund established by [NLnet](https://nlnet.nl) with financial support from the
European Commission's [Next Generation Internet](https://ngi.eu) programme, under
the aegis of [DG Communications Networks, Content and Technology](https://commission.europa.eu/about-european-commission/departments-and-executive-agencies/communications-networks-content-and-technology_en)
under grant agreement No [101135429](https://cordis.europa.eu/project/id/101135429).
