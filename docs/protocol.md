# Wyoming protocol

## Detection flow

```
Client → Describe
Server → Info(wake=[WakeProgram(models=[WakeModel(name="hey_mycroft", ...), ...])])

Client → Detect(names=["hey_mycroft", "wake_up"])
Client → AudioStart(rate=16000, width=2, channels=1)
       → AudioChunk (PCM)
       → AudioChunk ...
       → Detection(name="hey_mycroft", timestamp=1230)   ← on match
       → AudioChunk ...
       → AudioStop
Server → NotDetected                                      ← only if nothing matched
```

`Detect.names` selects the active wake words (engines are loaded on demand). An
empty or absent `Detect` uses the default wake word (`listener.wake_word`). Audio
is converted to 16 kHz / 16-bit / mono PCM automatically.

## Detection timestamp

`Detection.timestamp` is the elapsed audio in **milliseconds** since the last
`AudioStart`, accumulated from each chunk's duration. This matches
`wyoming-openwakeword` and still works when the client does not stamp its
`AudioChunk`s.

## De-duplication

A wake-word engine can keep matching for several consecutive chunks. To avoid a
flood of events, each wake word is reported **at most once per stream**. After it
fires, it is skipped until the next `AudioStart` resets the stream. `AudioStart`
also resets the audio clock and re-initializes every active engine.

## NotDetected

`NotDetected` is sent once, on `AudioStop`, and only if no wake word fired during
the stream (including the case where audio ends before any `Detect`).

## Errors

Any exception while handling an event is reported to the client as a Wyoming
`Error(text, code)` event, and the connection is closed.

---
[← Home Assistant](home_assistant.md) · [Home](index.md)
