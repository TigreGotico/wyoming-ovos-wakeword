# wyoming-ovos-wakeword documentation

Expose [OpenVoiceOS](https://openvoiceos.org) wake-word (hotword) plugins as a
[Wyoming protocol](https://github.com/OHF-voice/wyoming) wake service, for use
with Home Assistant, Rhasspy, and other Wyoming-compatible voice pipelines.

Every wake word defined under `hotwords` in `mycroft.conf` is advertised and can
be activated by the client. Engines are loaded on demand and fed 16 kHz / 16-bit /
mono audio; a match sends a `Detection`, and a stream that ends with no match
sends `NotDetected`.

## Pages

- **[Configuration](configuration.md)** — the `mycroft.conf` `hotwords` section,
  the default wake word, and zeroconf.
- **[Home Assistant](home_assistant.md)** — adding the bridge as a Wyoming
  wake-word service, including zeroconf discovery.
- **[Wyoming protocol](protocol.md)** — the detection flow, `Detection`
  timestamps, and de-duplication.

## Quickstart

```bash
pip install wyoming-ovos-wakeword ovos-ww-plugin-precise-lite

wyoming-ovos-wakeword --uri tcp://0.0.0.0:7893 --zeroconf
```

Home Assistant discovers the service over zeroconf, or add it by `host:7893` —
see [Home Assistant](home_assistant.md).

## Docker

```bash
docker build -t wyoming-ovos-wakeword .
docker run --rm -p 7893:7893 wyoming-ovos-wakeword \
    --uri tcp://0.0.0.0:7893 --zeroconf
```

The image installs the package (and its dependencies) from `pyproject.toml`; add
any wake-word engine plugin you intend to use to the image or mount its config.
