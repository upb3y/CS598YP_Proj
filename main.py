import os
import time
import argparse
from part1_structure_retreiver import get_file_structure_json
from part1_2_content_summary import summarize_files, init_model
from part2_organizer import generate_mapping
from part3_file_mover import organize_and_move_files


def main():
    parser = argparse.ArgumentParser(
        description="Run the entire pipeline: structure retrieval, summarization, organization, and file moving.")
    parser.add_argument("root_folder", help="Root folder to process.")
    parser.add_argument(
        "output_folder", help="Folder to store the organized files.")
    args = parser.parse_args()

    root_folder = args.root_folder
    output_folder = args.output_folder

    api_key, model = init_model()

    # Step 1: Retrieve file structure
    print("Step 1: Retrieving file structure...")
    structure_file = "file_structure.json"
    get_file_structure_json(root_folder)
    print(f"File structure saved to {structure_file}")

    # Step 2: Summarize file contents
    print("Step 2: Summarizing file contents...")
    summaries_file = "file_summaries.json"
    summarize_files(structure_file, summaries_file, root_folder, model)
    print(f"File summaries saved to {summaries_file}")

    time.sleep(60)

    # Step 3: Generate mapping for organization
    print("Step 3: Generating file organization mapping...")
    mapping_file = "file_mapping.json"
    generate_mapping(summaries_file, mapping_file, api_key)
    print(f"File mapping saved to {mapping_file}")

    # Step 4: Move files based on mapping
    print("Step 4: Moving files to organized structure...")
    organize_and_move_files(structure_file, mapping_file,
                            root_folder, output_folder)
    print("Files successfully organized.")


if __name__ == "__main__":
    main()
