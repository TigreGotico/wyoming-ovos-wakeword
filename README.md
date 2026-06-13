
# Wyoming OVOS WakeWord Bridge

expose OVOS wakeword plugins via wyoming for usage with the voice pee

![image](https://github.com/user-attachments/assets/3f495ea2-4322-4312-9ca1-c67e5b8bea54)

## Usage

```bash
$ wyoming-ovos-ww --help
usage: wyoming-ovos-wakeword [-h] [--uri URI] [--zeroconf [ZEROCONF]] [--debug] [--log-format LOG_FORMAT]

options:
  -h, --help            show this help message and exit
  --uri URI             unix:// or tcp://
  --zeroconf [ZEROCONF]
                        Enable discovery over zeroconf with optional name (default: ovos-ww-plugin)
  --debug               Log DEBUG messages
  --log-format LOG_FORMAT
                        Format for log messages

```

> wyoming-ovos-wakeword --uri tcp://0.0.0.0:7892 --zeroconf

wake words configs are read from `mycroft.conf`, anything under "hotwords" will be available via wyoming and loaded on demand

the default `mycroft.conf` is

```json
"hotwords": {
    "hey_mycroft": {
        "module": "ovos-ww-plugin-precise-lite",
        "model": "https://github.com/OpenVoiceOS/precise-lite-models/raw/master/wakewords/en/hey_mycroft.tflite",
        "expected_duration": 3,
        "trigger_level": 3,
        "sensitivity": 0.5,
        "listen": true,
        "fallback_ww": "hey_mycroft_precise"
    },
    "hey_mycroft_precise": {
        "module": "ovos-ww-plugin-precise",
        "version": "0.3",
        "model": "https://github.com/MycroftAI/precise-data/raw/models-dev/hey-mycroft.tar.gz",
        "expected_duration": 3,
        "trigger_level": 3,
        "sensitivity": 0.5,
        "listen": true,
        "fallback_ww": "hey_mycroft_vosk"
    },
    "hey_mycroft_vosk": {
        "module": "ovos-ww-plugin-vosk",
        "samples": ["hey mycroft", "hey microsoft", "hey mike roft", "hey minecraft"],
        "rule": "fuzzy",
        "listen": true,
        "fallback_ww": "hey_mycroft_pocketsphinx"
    },
    "hey_mycroft_pocketsphinx": {
        "module": "ovos-ww-plugin-pocketsphinx",
        "phonemes": "HH EY . M AY K R AO F T",
        "threshold": 1e-90,
        "lang": "en-us",
        "listen": true
    },
    "wake_up": {
        "module": "ovos-ww-plugin-vosk",
        "rule": "fuzzy",
        "samples": ["wake up"],
        "lang": "en-us",
        "wakeup": true,
        "fallback_ww": "wake_up_pocketsphinx"
    },
    "wake_up_pocketsphinx": {
        "module": "ovos-ww-plugin-pocketsphinx",
        "phonemes": "W EY K . AH P",
        "threshold": 1e-20,
        "lang": "en-us",
        "wakeup": true
    }
  },
```

---

## Credits

Developed by [TigreGótico](https://tigregotico.pt) for
[OpenVoiceOS](https://openvoiceos.org).

[![NGI0 Commons Fund](./ngi.png)](https://nlnet.nl/project/OpenVoiceOS)

This project was funded through the [NGI0 Commons Fund](https://nlnet.nl/commonsfund),
a fund established by [NLnet](https://nlnet.nl) with financial support from the
European Commission's [Next Generation Internet](https://ngi.eu) programme, under
the aegis of [DG Communications Networks, Content and Technology](https://commission.europa.eu/about-european-commission/departments-and-executive-agencies/communications-networks-content-and-technology_en)
under grant agreement No [101135429](https://cordis.europa.eu/project/id/101135429).
