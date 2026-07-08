# Audio Splitter VAD 🎙️✂️

A lightning-fast, production-ready Python library for audio silence removal and multithreaded chunking.

Built on top of Google's robust WebRTC Voice Activity Detection (VAD) engine, this tool allows you to strip silence from audio files and slice pure speech into manageable chunks. It is fully optimized for scale, featuring both I/O-bound multithreading for single massive files and CPU-bound multiprocessing for directories with thousands of files.

---

## Features

- **Silence Stripping:** Automatically detect and remove non-speech frames using WebRTC VAD.
- **Smart Slicing:** Yield continuous chunks of pure speech at any desired duration.
- **Universal Input:** Natively accepts `.mp3` and `.wav` files and automatically converts them into the 16-bit mono PCM format required by WebRTC.
- **Multithreaded Export:** Bypass the GIL by saving hundreds of chunks to disk concurrently.
- **Batch Processing:** Utilize all CPU cores via multiprocessing to process thousands of audio files at maximum speed.

---

## Installation

Install the package via `pip` (or `uv`):

```bash
pip install audio-splitter-vad
```

> **⚠️ System Requirement**
>
> This library uses `pydub` under the hood to decode `.mp3` files. You must have **FFmpeg** installed on your system and available in your `PATH`.

### Install FFmpeg

**macOS**

```bash
brew install ffmpeg
```

**Linux**

```bash
sudo apt install ffmpeg
```

**Windows**

Download FFmpeg from **gyan.dev** or install it with:

```powershell
winget install ffmpeg
```

---

# Quick Start

## 1. Memory-Efficient Generator (Streaming)

Ideal for streaming chunks directly to transcription APIs like Whisper or Google Cloud without saving them to disk.

```python
from splitter import Splitter

audio_splitter = Splitter()

# Yield 5-second chunks of pure speech (silence removed)
for chunk in audio_splitter.split(
    "podcast.mp3",
    slice_duration=5,
    strip_silence=True,
):
    print(f"Received {len(chunk)} bytes of pure speech!")
    # Send chunk to your API...
```

---

## 2. High-Speed Multithreaded Slicing (Single File)

Quickly split a single massive audio file into hundreds of `.wav` chunks on your hard drive.

```python
from splitter import Splitter

audio_splitter = Splitter()

# Save chunks concurrently using background threads
saved_files = audio_splitter.split_multithreaded(
    audio_path="massive_interview.wav",
    save_path="./clean_chunks",
    slice_duration=5,
    max_workers=8,
    strip_silence=True,
)

print(f"Successfully exported {len(saved_files)} chunks.")
```

---

## 3. Core-Max Batch Processing (Directories)

If you have a folder containing thousands of audio files, use multiprocessing instead of multithreading. This assigns an isolated VAD engine to every CPU core for maximum throughput.

```python
from batch_split import batch_process_directory

batch_process_directory(
    input_folder="./raw_podcasts",
    output_folder="./processed_datasets",
    strip_silence=True,
)
```

---

# Advanced Configuration

You can pass a custom WebRTC VAD engine when initializing `Splitter` to control how aggressively silence is removed.

| Mode | Description |
|------|-------------|
| `0` | Least aggressive (retains more background noise). |
| `1` | Light filtering. |
| `2` | Moderate filtering. |
| `3` | Most aggressive (removes nearly everything that is not speech). |

Example:

```python
import webrtcvad
from splitter import Splitter

# Less aggressive filtering
custom_vad = webrtcvad.Vad(1)

splitter = Splitter(vad_engine=custom_vad)
```
