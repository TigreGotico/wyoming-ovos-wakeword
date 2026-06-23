# Configuration

The bridge itself is configured with CLI flags; the **wake words** are configured
through `mycroft.conf` (the standard OVOS config stack), read at startup.

## CLI

| Argument | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--uri` | No | `stdio://` | `tcp://HOST:PORT`, `unix:///path`, or `stdio://` |
| `--zeroconf` | No | disabled | announce over mDNS/zeroconf (optional service name, default `ovos-ww-plugin`) |
| `--debug` | No | `False` | DEBUG-level logging |
| `--log-format` | No | `%(levelname)s:%(name)s:%(message)s` | Python log format |
| `--version` | No | — | print version and exit |

`--zeroconf` requires a `tcp://` URI; the service registers as
`_wyoming._tcp.local.`.

## Wake words

Wake words are read from `mycroft.conf` under `hotwords`. Every entry is
advertised in the `Info` response and is selectable by name; the engine for a wake
word is created the first time it is activated.

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
    }
  }
}
```

## Default wake word

When a client sends a `Detect` event without names (or never sends one), the
bridge uses `listener.wake_word` as the active wake word. A `Detect` that lists
names replaces the active set with exactly those.

## Supported engines

Any plugin implementing `HotWordEngine` from
`ovos_plugin_manager.templates.hotwords`, e.g. `ovos-ww-plugin-precise-lite`,
`ovos-ww-plugin-vosk`, `ovos-ww-plugin-precise`, `ovos-ww-plugin-pocketsphinx`.
Install the engine alongside the bridge — it is not pulled in automatically.
