import os

# os.add_dll_directory(r"C:/ffmpeg_windows/bin")
import shutil

from audio_splitter_vad.splitter import Splitter


def run_tests():
    input_file = "./test_batch/test.mp3"

    # 1. Ensure the test file exists before running
    if not os.path.exists(input_file):
        print(
            f"❌ ERROR: Test file not found. Please place a valid audio file at '{input_file}'."
        )
        return

    print(f"✅ Found {input_file}. Initializing Splitter...\n")
    splitter = Splitter()

    # =========================================================
    # TEST 1: Sequential Generator WITH Silence Removal
    # =========================================================
    print("=== TEST 1: Sequential Split (strip_silence=True) ===")
    seq_output_dir = "./test_output_seq"

    # Clean up old test folders if they exist
    if os.path.exists(seq_output_dir):
        shutil.rmtree(seq_output_dir)

    chunks_yielded = 0
    # Process the file
    for chunk in splitter.split(
        input_file, slice_duration=5, save_path=seq_output_dir, strip_silence=True
    ):
        # Assertions/Checks inside the generator
        assert isinstance(chunk, bytes), "Chunk should be raw bytes"
        assert len(chunk) > 0, "Chunk should not be empty"
        chunks_yielded += 1

    print(
        f"✅ PASS: Yielded and saved {chunks_yielded} pure-speech chunks to '{seq_output_dir}'.\n"
    )

    # =========================================================
    # TEST 2: Multithreaded Processing WITHOUT Silence Removal
    # =========================================================
    print("=== TEST 2: Multithreaded Split (strip_silence=False) ===")
    multi_output_dir = "./test_output_multi"

    # Clean up old test folders if they exist
    if os.path.exists(multi_output_dir):
        shutil.rmtree(multi_output_dir)

    # Process the file
    saved_files = splitter.split_multithreaded(
        input_file, save_path=multi_output_dir, slice_duration=5, strip_silence=False
    )

    # Assertions
    assert isinstance(saved_files, list), "Should return a list of file paths"
    if saved_files:
        assert os.path.exists(saved_files[0]), (
            "Saved files should actually exist on disk"
        )

    print(
        f"✅ PASS: Multithreaded save completed. Created {len(saved_files)} files in '{multi_output_dir}'."
    )
    print("\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    run_tests()
