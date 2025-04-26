import argparse
import json
import os


def get_file_structure_json(root_folder):
    """
    Recursively traverses a folder and returns a JSON-formatted list of non-hidden files
    with assigned unique IDs and relative paths.

    Hidden files and directories (starting with a dot) are ignored.

    Parameters:
        root_folder (str): The root folder to scan. Can be relative or absolute path.

    Returns:
        str: A JSON string representing a list of files.
             Each file is represented as a dictionary with:
             - 'id' (int): Unique ID for the file
             - 'path' (str): Path relative to the root_folder

    Example:
        >>> get_file_structure_json("../data")
        '[{"id": 1, "path": "file1.txt"}, {"id": 2, "path": "subdir/file2.txt"}]'
    """
    file_list = []
    file_id = 1

    for dirpath, dirnames, filenames in os.walk(root_folder):
        # Skip hidden directories in-place
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        # Skip hidden files
        filenames = [f for f in filenames if not f.startswith('.')]

        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(full_path, root_folder)
            file_entry = {
                "id": file_id,
                "path": relative_path
            }
            file_list.append(file_entry)
            file_id += 1

    with open("file_structure.json", "w", encoding="utf-8") as out:
        json.dump(file_list, out, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate file structure JSON from a folder (ignoring hidden files).")
    parser.add_argument(
        "folder", help="Relative or absolute path to the folder")
    args = parser.parse_args()

    folder_path = args.folder
    get_file_structure_json(folder_path)
