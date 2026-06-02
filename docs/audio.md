# Audio capture during screen recording

Starting with PR1, the recorder can capture audio alongside the screen.
The behaviour is controlled by the `recorder` section of your
`config.yaml`:

```yaml
recorder:
  fps: 30
  audio_mode: both         # one of: none | mic | system | both
  mic_device: ""           # leave empty for OS default
  system_device: ""        # leave empty for OS default loopback (Stereo Mix on Windows)
```

## audio_mode

| Mode | What gets captured |
|------|--------------------|
| `none` | Video only (legacy behaviour). |
| `mic` | Microphone only. |
| `system` | System audio ("what you hear") only. |
| `both` | Mic + System mixed into one AAC track. Default. |

## Selecting devices

### Windows (DirectShow)

`mic_device` / `system_device` are the exact dshow device names. Discover them with:

```
ffmpeg -list_devices true -f dshow -i dummy
```

Examples:

```yaml
mic_device: "Microphone (Realtek(R) Audio)"
system_device: "Stereo Mix (Realtek(R) Audio)"
```

If Stereo Mix is missing, enable it under **Sound → Recording → right-click → Show Disabled Devices**.

### macOS (AVFoundation)

`mic_device` is the integer index reported by:

```
ffmpeg -f avfoundation -list_devices true -i ""
```

macOS has no built-in loopback. Install [BlackHole](https://existential.audio/blackhole/)
(or Soundflower / an aggregate device) to capture system audio, then point
`system_device` at it.

### Linux (PulseAudio)

`mic_device` is a PulseAudio source name; `system_device` is typically the
monitor of your default sink:

```yaml
mic_device: "alsa_input.pci-0000_00_1f.3.analog-stereo"
system_device: "alsa_output.pci-0000_00_1f.3.analog-stereo.monitor"
```

List sources with:

```
pactl list short sources
```

The string `@DEFAULT_MONITOR@` (used when `system_device` is empty on Linux)
expands to the monitor of whatever sink is currently default.

## Migration

If you're upgrading from a pre-PR1 config, the loader will automatically add
`audio_mode: both`, `mic_device: ""`, `system_device: ""` to your `recorder:`
section and write a `.pre-pr1.bak` backup next to your config file.
