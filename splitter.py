import os
import wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Generator, List, Optional, Tuple

import webrtcvad
from pydub import AudioSegment


class Splitter:
    def __init__(self, vad_engine: Optional[webrtcvad.Vad] = None) -> None:
        if vad_engine is None:
            self.vad = webrtcvad.Vad(3)
        else:
            self.vad = vad_engine

    def slice_audio(
        self, audio_bytes: bytes, sample_rate: int, chunk_seconds: int = 5
    ) -> Generator[bytes, None, None]:
        """
        A generator that yields chunks of audio based on a desired duration in seconds.
        """
        # Calculate how many bytes make up the target duration
        # 16-bit audio uses 2 bytes per sample
        bytes_per_second = sample_rate * 2
        bytes_per_chunk = bytes_per_second * chunk_seconds

        # Slice the byte string and yield it chunk by chunk
        for i in range(0, len(audio_bytes), bytes_per_chunk):
            chunk = audio_bytes[i : i + bytes_per_chunk]
            yield chunk

    def remove_silence(
        self, audio_bytes: bytes, sample_rate: int, frame_duration_ms: int = 30
    ) -> bytes:
        """
        Analyzes raw audio in frames. Throws away silence and
        returns a new byte string containing ONLY active speech.
        """
        samples_per_frame = int(sample_rate * (frame_duration_ms / 1000.0))
        bytes_per_frame = samples_per_frame * 2  # 16-bit audio uses 2 bytes per sample.
        speech_frames = []
        for i in range(0, len(audio_bytes), bytes_per_frame):
            frame = audio_bytes[i : i + bytes_per_frame]
            if (
                len(frame) < bytes_per_frame
            ):  # Skip the last frame if it's not exactly 30ms
                break
            is_speech = self.vad.is_speech(frame, sample_rate)
            if is_speech:
                speech_frames.append(frame)
        # Stitch the speech frames together and return the pure-speech bytes
        return b"".join(speech_frames)

    def open_audio(self, audio_path: str) -> Tuple[bytes, int]:
        """
        Universal loader: Reads MP3 or WAV, standardizes it to Mono 16-bit PCM,
        and ensures a WebRTC-compatible sample rate.
        """
        # pydub automatically detects if it's an mp3, wav, flac, etc.
        audio = AudioSegment.from_file(audio_path)

        # WebRTC strictly requires 1 channel (Mono) and 2 bytes per sample (16-bit)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)

        sample_rate = audio.frame_rate

        # WebRTC only supports these 4 sample rates
        if sample_rate not in [8000, 16000, 32000, 48000]:
            # Standardize odd sample rates (like 44100 Hz from MP3s) down to 16000 Hz
            audio = audio.set_frame_rate(16000)
            sample_rate = 16000

        return audio.raw_data, sample_rate

    def save_chunk_wav(
        self, chunk_bytes: bytes, sample_rate: int, file_path: str
    ) -> str:
        """
        Saves raw 16-bit PCM bytes directly to a .wav file.
        This is lightning fast because it requires no re-encoding.
        """
        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(chunk_bytes)
        return file_path

    def split(
        self,
        audio_path: str,
        slice_duration: int = 5,
        frame_duration_ms: int = 30,
        save_path: Optional[str] = None,
        strip_silence: bool = True,
    ) -> Generator[bytes, None, None]:
        """
        Yields pure speech chunks. If save_path is provided, saves them as WAV files sequentially.
        """
        raw_audio_bytes, sample_rate = self.open_audio(audio_path)
        speech_only_bytes = (
            self.remove_silence(raw_audio_bytes, sample_rate, frame_duration_ms)
            if strip_silence
            else raw_audio_bytes
        )
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        if save_path and not os.path.exists(save_path):
            os.makedirs(save_path)
        chunk_index = 1
        for chunk in self.slice_audio(speech_only_bytes, sample_rate, slice_duration):
            if save_path:
                file_name = f"{base_name}_{chunk_index}.wav"
                full_path = os.path.join(save_path, file_name)
                self.save_chunk_wav(chunk, sample_rate, full_path)
            yield chunk
            chunk_index += 1

    def split_multithreaded(
        self,
        audio_path: str,
        save_path: str,
        slice_duration: int = 5,
        frame_duration_ms: int = 30,
        max_workers: int = 8,
        strip_silence: bool = True,
    ) -> List[str]:
        """
        Speed-optimized pipeline. Extracts silence sequentially (CPU bound),
        then uses threads to write the WAV files to disk concurrently (I/O bound).
        """
        raw_audio_bytes, sample_rate = self.open_audio(audio_path)

        print("Extracting pure speech...")
        speech_only_bytes = (
            self.remove_silence(raw_audio_bytes, sample_rate, frame_duration_ms)
            if strip_silence
            else raw_audio_bytes
        )

        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # Convert generator to a list to dispatch to threads
        chunks = list(self.slice_audio(speech_only_bytes, sample_rate, slice_duration))
        print(
            f"Threading export of {len(chunks)} WAV chunks using {max_workers} workers..."
        )

        saved_files = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for index, chunk in enumerate(chunks, start=1):
                file_name = f"{base_name}_{index}.wav"
                full_path = os.path.join(save_path, file_name)

                # Submit the WAV writing task to the thread pool
                future = executor.submit(
                    self.save_chunk_wav, chunk, sample_rate, full_path
                )
                futures[future] = full_path

            for future in as_completed(futures):
                try:
                    result_path = future.result()
                    saved_files.append(result_path)
                except Exception as e:
                    print(f"Error saving {futures[future]}: {e}")

        return sorted(saved_files)
