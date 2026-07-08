import glob
import os
import shutil

from batch_split import batch_process_directory


def run_batch_tests():
    source_test_file = "./test.mp3"

    # 1. Ensure the source file exists
    if not os.path.exists(source_test_file):
        print(
            f"❌ ERROR: Source test file '{source_test_file}' not found. Please provide one."
        )
        return

    input_dir = "./test_batch"
    output_dir = "./test_batch_output"

    # 2. Clean up any previous test runs
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    print(f"Created 3 files in '{input_dir}' for processing.\n")

    # =========================================================
    # TEST: Multiprocessing Directory (strip_silence=True)
    # =========================================================
    print("=== TEST 3: Multiprocessing Batch Directory ===")

    # Run the batch processor!
    batch_process_directory(
        input_folder=input_dir, output_folder=output_dir, strip_silence=True
    )

    # 4. Verify the results
    output_files = glob.glob(os.path.join(output_dir, "*.wav"))

    # Group the output files by their original base name to check distribution
    files_per_clone = {1: 0, 2: 0, 3: 0}
    for file_path in output_files:
        if "podcast_clone_1" in file_path:
            files_per_clone[1] += 1
        if "podcast_clone_2" in file_path:
            files_per_clone[2] += 1
        if "podcast_clone_3" in file_path:
            files_per_clone[3] += 1

    print("\n--- RESULTS ---")
    if len(output_files) > 0:
        print(
            f"✅ PASS: Generated {len(output_files)} total files across the 3 inputs."
        )
        print(f"  - Clone 1 yielded: {files_per_clone[1]} chunks")
        print(f"  - Clone 2 yielded: {files_per_clone[2]} chunks")
        print(f"  - Clone 3 yielded: {files_per_clone[3]} chunks")
    else:
        print("⚠️ WARNING: Batch executed without crashing, but 0 chunks were saved.")
        print(
            "This usually means your 'test.mp3' file is either entirely silent, or too short to hit the 5-second chunk limit."
        )

    print(f"\n🎉 Batch test completed! You can inspect the outputs in '{output_dir}'.")


# Note: This __main__ block is ABSOLUTELY CRITICAL when testing
# multiprocessing on Windows, otherwise the script will infinitely loop.
if __name__ == "__main__":
    run_batch_tests()
