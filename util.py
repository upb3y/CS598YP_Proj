import os
import json
import hashlib
from typing import Dict, Any, Optional, Tuple, Set, List
import zss

def calculate_sha256(filepath: str, buffer_size: int = 65536) -> Optional[str]:
    """Calculates the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while True:
                data = f.read(buffer_size)
                if not data:
                    break
                sha256_hash.update(data)
        return sha256_hash.hexdigest()
    except OSError as e:
        print(f"Warning: Could not read file '{filepath}' for hashing: {e}")
        return None
    except Exception as e:
        print(f"Warning: Unexpected error hashing file '{filepath}': {e}")
        return None


def create_directory_tree_with_hashes(start_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generates a dictionary representing the directory tree, including SHA-256 hashes for files.

    Args:
        start_path: The root directory path. Uses CWD if None.

    Returns:
        A dictionary representing the tree.
        Files: {"type": "file", "hash": "sha256_hash_or_none"}
        Dirs: {"type": "directory", "children": {...}}
        Errors: {"type": "error", "message": "..."}
        Returns an empty dict if start_path is invalid.
    """
    if start_path is None:
        start_path = os.getcwd()
    elif not os.path.isdir(start_path):
        print(f"Error: Path '{start_path}' is not a valid directory.")
        return {}

    abs_start_path = os.path.abspath(start_path)

    def _build_tree_recursive(current_abs_path: str) -> Dict[str, Any]:
        tree_node: Dict[str, Any] = {}
        try:
            items = os.listdir(current_abs_path)
            items.sort()
        except OSError as e:
            print(f"Critical Warning: Cannot list directory '{current_abs_path}': {e}")
            return {"__listing_error__": f"Access denied or error: {e}"} 

        for item_name in items:
            item_abs_path = os.path.join(current_abs_path, item_name)
            try:
                if os.path.isdir(item_abs_path):
                    children = _build_tree_recursive(item_abs_path)
                    tree_node[item_name] = {"type": "directory", "children": children}
                elif os.path.isfile(item_abs_path):
                    file_hash = calculate_sha256(item_abs_path)
                    tree_node[item_name] = {"type": "file", "hash": file_hash}

            except OSError as e:
                 print(f"Warning: Could not access item '{item_abs_path}': {e}")
                 tree_node[item_name] = {"type": "error", "message": f"Error accessing item: {e}"}
            except Exception as e:
                 print(f"Warning: Unexpected error processing '{item_abs_path}': {e}")
                 tree_node[item_name] = {"type": "error", "message": f"Unexpected error: {e}"}


        return tree_node

    root_contents = _build_tree_recursive(abs_start_path)
    return root_contents

def _flatten_tree_with_hashes(
    tree_dict: Dict[str, Any],
    current_path: str = ".",
    separator: str = "/"
) -> Set[Tuple[str, str, Optional[str]]]:
    """
    Flattens a directory tree dictionary (with hash structure)
    into a set of (path, type, hash) tuples. Hash is None for non-files.
    Uses POSIX-style separators ('/') for consistency.
    """
    items: Set[Tuple[str, str, Optional[str]]] = set()
    current_path = current_path.replace(os.path.sep, separator)
    base_path = "" if current_path == "." else current_path + separator

    for name, content in tree_dict.items():
        item_path = base_path + name
        item_type = content.get("type") if isinstance(content, dict) else "unknown" 
        item_hash = content.get("hash") if isinstance(content, dict) and item_type == "file" else None

        if item_type == "directory":
            items.add((item_path, "directory", None))
            children = content.get("children", {})
            if isinstance(children, dict): 
                 items.update(_flatten_tree_with_hashes(children, current_path=item_path, separator=separator))
            else:
                 print(f"Warning: Expected dictionary for children of '{item_path}', got {type(children)}")
        elif item_type == "file":
            items.add((item_path, "file", item_hash))
        elif item_type == "error":
            items.add((item_path, "error", content.get("message")))

    return items


def _dict_to_zss_node_recursive_hashed(node_label: str, node_content: Dict[str, Any]) -> Tuple[zss.Node, int]:
    """
    Recursively converts a dictionary representation (with hash structure)
    into a zss.Node structure. Label is the file/dir name. Also counts nodes.
    """
    if not zss: raise ImportError("zss library not available.")

    current_node = zss.Node(node_label) 
    node_count = 1
    node_type = node_content.get("type")

    if node_type == "directory":
        children_dict = node_content.get("children", {})
        if isinstance(children_dict, dict):
            sorted_items = sorted(children_dict.items())
            for child_label, child_content in sorted_items:
                if isinstance(child_content, dict):
                    child_node, child_node_count = _dict_to_zss_node_recursive_hashed(child_label, child_content)
                    current_node.addkid(child_node)
                    node_count += child_node_count
                else:
                     print(f"Warning: Skipping malformed child '{child_label}' under '{node_label}'. Expected dict, got {type(child_content)}.")
    return current_node, node_count

def calculate_tree_similarity_zss_hashed(
    tree_dict1: Dict[str, Any],
    tree_dict2: Dict[str, Any],
    root_label: str = "."
) -> float:
    """Calculates structural similarity using zss library (TED) on hashed tree structures."""
    if not zss: return -1.0
    try:
        root_content1 = {"type": "directory", "children": tree_dict1}
        root_content2 = {"type": "directory", "children": tree_dict2}

        zss_tree1, size1 = _dict_to_zss_node_recursive_hashed(root_label, root_content1)
        zss_tree2, size2 = _dict_to_zss_node_recursive_hashed(root_label, root_content2)

        if size1 == 0 and size2 == 0: return 1.0
        distance = zss.simple_distance(zss_tree1, zss_tree2)
        max_possible_distance = size1 + size2
        if max_possible_distance == 0: return 1.0 if distance == 0 else 0.0
        similarity = 1.0 - (distance / max_possible_distance)
        return max(0.0, min(similarity, 1.0))
    except Exception as e:
        print(f"Error during zss calculation (hashed): {e}")
        return -1.0


def evaluate_restructuring_with_hashes(
    original_tree_dict: Dict[str, Any],
    restructured_tree_dict: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Compares two directory tree dictionaries (containing file hashes)
    to evaluate restructuring performance.

    Calculates TED-based similarity and detailed change counts (added, deleted,
    moved, renamed files/directories) using file hashes for identity tracking.

    Args:
        original_tree_dict: Hashed dictionary representation of the original tree.
        restructured_tree_dict: Hashed dictionary representation of the restructured tree.

    Returns:
        A dictionary containing evaluation metrics, or None on failure.
    """
    results: Dict[str, Any] = {}
    separator = "/" # Use POSIX style

    # 1. Calculate TED-based Similarity (based on names/structure)
    ted_similarity = calculate_tree_similarity_zss_hashed(original_tree_dict, restructured_tree_dict)
    if ted_similarity < 0:
        print("Evaluation failed due to error in similarity calculation.")
        return None
    results["ted_similarity"] = ted_similarity
    print(ted_similarity)
    # 2. Detailed Change Analysis using Hashes
    try:
        items1 = _flatten_tree_with_hashes(original_tree_dict, separator=separator)
        items2 = _flatten_tree_with_hashes(restructured_tree_dict, separator=separator)

        # --- File Analysis based on Hash ---
        files1_map = {item[2]: item[0] for item in items1 if item[1] == 'file' and item[2] is not None} # hash -> path
        files2_map = {item[2]: item[0] for item in items2 if item[1] == 'file' and item[2] is not None} # hash -> path
        hashes1 = set(files1_map.keys())
        hashes2 = set(files2_map.keys())

        deleted_hashes = hashes1 - hashes2
        added_hashes = hashes2 - hashes1
        common_hashes = hashes1.intersection(hashes2)

        files_deleted = len(deleted_hashes)
        files_added = len(added_hashes)
        files_unchanged = 0
        files_moved = 0
        files_renamed = 0
        files_moved_renamed = 0
        # Store paths for optional output
        deleted_file_paths = [files1_map[h] for h in deleted_hashes]
        added_file_paths = [files2_map[h] for h in added_hashes]
        moved_renamed_details = []


        for h in common_hashes:
            path1 = files1_map[h]
            path2 = files2_map[h]
            if path1 == path2:
                files_unchanged += 1
            else:
                # Classify the move/rename
                basename1 = path1.split(separator)[-1]
                basename2 = path2.split(separator)[-1]
                dirname1 = separator.join(path1.split(separator)[:-1])
                dirname2 = separator.join(path2.split(separator)[:-1])

                moved = dirname1 != dirname2
                renamed = basename1 != basename2

                detail = {"hash": h, "original_path": path1, "new_path": path2}
                if moved and renamed:
                    files_moved_renamed += 1
                    detail["change_type"] = "moved_renamed"
                elif moved:
                    files_moved += 1
                    detail["change_type"] = "moved"
                elif renamed:
                    files_renamed += 1
                    detail["change_type"] = "renamed"
                moved_renamed_details.append(detail)


        results["files_added"] = files_added
        results["files_deleted"] = files_deleted
        results["files_unchanged"] = files_unchanged
        results["files_moved"] = files_moved
        results["files_renamed"] = files_renamed
        results["files_moved_renamed"] = files_moved_renamed

        # --- Directory Analysis based on Path (heuristic) ---
        dirs1_paths = {item[0] for item in items1 if item[1] == 'directory'}
        dirs2_paths = {item[0] for item in items2 if item[1] == 'directory'}

        deleted_dirs_cand = dirs1_paths - dirs2_paths
        added_dirs_cand = dirs2_paths - dirs1_paths
        unchanged_dir_paths = dirs1_paths.intersection(dirs2_paths)

        dirs_moved = 0
        dirs_renamed = 0
        matched_added_dirs = set()
        processed_deleted_dirs = set()
        moved_renamed_dir_details = []


        for dd in list(deleted_dirs_cand):
            if dd in processed_deleted_dirs: continue
            dd_basename = dd.split(separator)[-1]
            dd_dirname = separator.join(dd.split(separator)[:-1])

            # Check moves first
            potential_moves = {ad for ad in added_dirs_cand if ad not in matched_added_dirs and ad.split(separator)[-1] == dd_basename}
            if potential_moves:
                dirs_moved += 1
                match = potential_moves.pop() # Take one
                matched_added_dirs.add(match)
                processed_deleted_dirs.add(dd)
                moved_renamed_dir_details.append({"type": "moved", "original_path": dd, "new_path": match})
                continue

            # Check renames
            potential_renames = {ad for ad in added_dirs_cand if ad not in matched_added_dirs and separator.join(ad.split(separator)[:-1]) == dd_dirname}
            if potential_renames:
                dirs_renamed += 1
                match = potential_renames.pop() # Take one
                matched_added_dirs.add(match)
                processed_deleted_dirs.add(dd)
                moved_renamed_dir_details.append({"type": "renamed", "original_path": dd, "new_path": match})
                continue

        results["dirs_added"] = len(added_dirs_cand - matched_added_dirs)
        results["dirs_deleted"] = len(deleted_dirs_cand - processed_deleted_dirs)
        results["dirs_unchanged"] = len(unchanged_dir_paths)
        results["dirs_moved"] = dirs_moved
        results["dirs_renamed"] = dirs_renamed

        # Optional: Store detailed path lists
        results["details"] = {
             "deleted_files": deleted_file_paths,
             "added_files": added_file_paths,
             "moved_renamed_files": moved_renamed_details,
             "deleted_dirs": list(deleted_dirs_cand - processed_deleted_dirs),
             "added_dirs": list(added_dirs_cand - matched_added_dirs),
             "moved_renamed_dirs": moved_renamed_dir_details,
             "unchanged_dirs": list(unchanged_dir_paths),
        }


    except Exception as e:
        print(f"Error during detailed diff calculation with hashes: {e}")
        # import traceback # For debugging
        # traceback.print_exc()
        results["diff_error"] = str(e)
        # Clear or indicate error for counts
        keys_to_clear = [
            "files_added", "files_deleted", "files_unchanged", "files_moved",
            "files_renamed", "files_moved_renamed", "dirs_added", "dirs_deleted",
            "dirs_unchanged", "dirs_moved", "dirs_renamed", "details"
        ]
        for key in keys_to_clear: results[key] = None

    return results

# # --- Example Usage ---
# if __name__ == "__main__":
#     # Create dummy directories and files for testing
#     # Make sure these paths exist or adapt the example
#     base_dir = "eval_test_temp"
#     orig_dir = os.path.join(base_dir, "original")
#     rest_dir = os.path.join(base_dir, "restructured")

#     # Clean up previous runs
#     import shutil
#     if os.path.exists(base_dir):
#         shutil.rmtree(base_dir)

#     # Create Original Structure
#     os.makedirs(os.path.join(orig_dir, "docs", "images"), exist_ok=True)
#     os.makedirs(os.path.join(orig_dir, "src"), exist_ok=True)
#     with open(os.path.join(orig_dir, "docs", "report_v1.txt"), "w") as f: f.write("Report Content Alpha")
#     with open(os.path.join(orig_dir, "docs", "project_notes.md"), "w") as f: f.write("Notes Content Beta")
#     with open(os.path.join(orig_dir, "docs", "images", "logo.png"), "w") as f: f.write("PNG Data Gamma") # Simple text for demo hash
#     with open(os.path.join(orig_dir, "src", "main.py"), "w") as f: f.write("print('Hello')")
#     with open(os.path.join(orig_dir, "src", "utils.py"), "w") as f: f.write("def helper(): pass")
#     with open(os.path.join(orig_dir, "misc_file.tmp"), "w") as f: f.write("Temporary data")

#     # Create Restructured Structure (mimicking the previous example)
#     os.makedirs(os.path.join(rest_dir, "documents", "reports"), exist_ok=True)
#     os.makedirs(os.path.join(rest_dir, "documents", "assets"), exist_ok=True)
#     os.makedirs(os.path.join(rest_dir, "source_code", "helpers"), exist_ok=True)
#     # report_v1 moved and renamed (content same)
#     with open(os.path.join(rest_dir, "documents", "reports", "report_final.txt"), "w") as f: f.write("Report Content Alpha")
#     # project_notes renamed (content same)
#     with open(os.path.join(rest_dir, "documents", "notes.md"), "w") as f: f.write("Notes Content Beta")
#      # logo.png moved (content same)
#     with open(os.path.join(rest_dir, "documents", "assets", "logo.png"), "w") as f: f.write("PNG Data Gamma")
#     # main.py renamed (content same)
#     with open(os.path.join(rest_dir, "source_code", "main_app.py"), "w") as f: f.write("print('Hello')")
#      # utils.py moved and renamed (content same)
#     with open(os.path.join(rest_dir, "source_code", "helpers", "utilities.py"), "w") as f: f.write("def helper(): pass")
#     # misc_file.tmp is deleted
#     # a new file added
#     with open(os.path.join(rest_dir, "README.md"), "w") as f: f.write("New Readme")


#     print(f"Generating tree with hashes for: {orig_dir}")
#     original_tree_h = create_directory_tree_with_hashes(orig_dir)
#     print("\nOriginal Tree (Hashed):")
#     print(json.dumps(original_tree_h, indent=2))


#     print(f"\nGenerating tree with hashes for: {rest_dir}")
#     restructured_tree_h = create_directory_tree_with_hashes(rest_dir)
#     print("\nRestructured Tree (Hashed):")
#     print(json.dumps(restructured_tree_h, indent=2))


#     print("\n--- Evaluating Restructuring with Hashes ---")
#     evaluation_results_h = evaluate_restructuring_with_hashes(original_tree_h, restructured_tree_h)

#     if evaluation_results_h:
#         print("\nEvaluation Metrics (Hashed):")
#         # Nicer printing, excluding the detailed lists initially
#         for key, value in evaluation_results_h.items():
#             if key != "details":
#                 print(f"- {key}: {value}")
#     else:
#          print("Evaluation failed.")

#     # Clean up dummy directories
#     print("\nCleaning up temporary directories...")
#     shutil.rmtree(base_dir)