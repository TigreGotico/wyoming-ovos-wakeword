# Home Assistant integration

The bridge speaks the Wyoming protocol, so Home Assistant talks to it through the
[Wyoming integration](https://www.home-assistant.io/integrations/wyoming/).

## Add the service

Run the bridge on a TCP URI reachable from Home Assistant. With `--zeroconf` it is
discovered automatically:

```bash
wyoming-ovos-wakeword --uri tcp://0.0.0.0:7893 --zeroconf
```

Home Assistant surfaces a discovered **Wyoming Protocol** entry. Confirm it to
add the wake-word service. Without zeroconf, add it manually through **Settings →
Devices & Services → Add Integration → Wyoming Protocol** using the bridge host
and port (`7893` above).

The wake words come from your `mycroft.conf` `hotwords`. Select one per
[Assist pipeline](https://www.home-assistant.io/voice_control/) / satellite under
**Wake word**.

## Notes

- The stream stays open for the whole session. The bridge reports a `Detection`
  the moment a wake word matches and continues listening.
- Each wake word is reported at most once per audio stream (see
  [protocol](protocol.md)).
- Audio is converted to 16 kHz / 16-bit / mono internally, so the satellite's
  capture format does not need to match the engine.

---
[← Configuration](configuration.md) · [Home](index.md) · [Wyoming protocol →](protocol.md)
