import glob
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

# Assuming your Splitter class is saved in a file called audio_tools.py
from splitter import Splitter


def process_single_file(
    input_path: str, output_dir: str, strip_silence: bool = True
) -> str:
    """
    This function is sent to a completely isolated CPU core.
    It instantiates its own VAD engine, making it 100% safe.
    """
    try:
        # 1. Create a localized Splitter for this core
        local_splitter = Splitter()

        # 2. We use the standard sequential split, because
        # doing threads inside of processes is overkill here.
        chunk_count = 0
        for _ in local_splitter.split(
            input_path,
            slice_duration=5,
            save_path=output_dir,
            strip_silence=strip_silence,
        ):
            chunk_count += 1

        return f"SUCCESS: {os.path.basename(input_path)} -> {chunk_count} chunks"

    except Exception as e:
        return f"ERROR: Failed on {os.path.basename(input_path)}. Reason: {e}"


def batch_process_directory(input_folder: str, output_folder: str, strip_silence=True):
    """
    Reads a folder of audio files and processes them across all CPU cores.
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Gather all WAV and MP3 files in the folder
    audio_files = []
    audio_files.extend(glob.glob(os.path.join(input_folder, "*.wav")))
    audio_files.extend(glob.glob(os.path.join(input_folder, "*.mp3")))

    total_files = len(audio_files)
    print(f"Found {total_files} files to process.")

    # Automatically detect how many cores your computer has
    max_cores = os.cpu_count() or 4
    print(f"Spinning up {max_cores} parallel CPU processes...\n")

    # Launch the Multiprocessing pool
    with ProcessPoolExecutor(max_workers=max_cores) as executor:
        futures = {}

        # Submit all files to the pool
        for file_path in audio_files:
            future = executor.submit(
                process_single_file,
                file_path,
                output_folder,
                strip_silence=strip_silence,
            )
            futures[future] = file_path

        # Track progress as files finish
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result_message = future.result()
            print(f"[{completed}/{total_files}] {result_message}")


if __name__ == "__main__":
    INPUT_DIR = "./massive_audio_folder"
    OUTPUT_DIR = "./clean_audio_chunks"

    batch_process_directory(INPUT_DIR, OUTPUT_DIR)
