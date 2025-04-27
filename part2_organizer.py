"""
This script generates a mapping JSON file that suggests new folder paths and names for files based on their summaries.
It uses the Gemini API to generate these paths in a continuous session, ensuring that the context of previous files is maintained throughout the process.

Input:
- A JSON file containing file metadata and summaries.

Output:
- A JSON file mapping each file ID to a new folder path and suggested new name.

Arguments:
- `input_file`: Path to the input JSON file containing file metadata and summaries.
- `output_file`: Path to save the generated mapping JSON file.
- `api_key`: The Gemini API key, which can be provided as a command-line argument or through the environment variable `GEMINI_API_KEY`.

Sample call:
    
    ```bash python part2_organizer.py input_file.json output_file.json --api_key YOUR_API_KEY
"""

import argparse
import json
import os
import re
import google.generativeai as genai
from typing import Optional, Tuple, List, Dict
from dotenv import load_dotenv

load_dotenv()

def generate_paths_with_session(file_data: List[Dict], api_key: str) -> Tuple[Dict[int, str], Dict[int, str]]:
    """
    Use a continuous session with Gemini API to generate folder paths for all files.
    
    Parameters:
        file_data (List[Dict]): List of file metadata including summaries
        api_key (str): The Gemini API key
        
    Returns:
        Tuple[Dict[int, str], Dict[int, str]]: A tuple containing two dictionaries:
            - paths: Dictionary mapping file IDs to generated folder paths
            - new_names: Dictionary mapping file IDs to suggested new names
    """
    # Configure the Gemini API
    genai.configure(api_key=api_key)
    
    # Create a model object for chat
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    # Start a chat session
    chat = model.start_chat(history=[])
    
    # First, provide context with all files
    context_prompt = "I need to organize the following files into appropriate folder structures:\n\n"
    
    for file in file_data:
        file_id = file.get("id")
        filename = file.get("filename")
        original_path = file.get("path", "")
        summary = file.get("summary", "")
        context_prompt += f"File {file_id}: {filename}\nSummary: {summary}\n\n"
    
    context_prompt += "Please help me organize these files into logical folder structures."
    
    # Send the context prompt
    response = chat.send_message(context_prompt)
    
    paths = {}
    new_names = {}
    
    # Now ask for paths one by one
    for file in file_data:
        file_id = file.get("id")
        filename = file.get("filename")
        summary = file.get("summary", "")
        
        path_prompt = f"""
        For File {file_id}: {filename}
        Summary: {summary}
        
        Suggest ONE appropriate folder path where this file should be stored. 
        Reply with ONLY the folder path, no explanation.
        
        Examples of folder paths:
        - Financial/2025
        - Reports
        - Images/Family
        - Documents/Personal
        """

        file_rename_prompt = f"""
        For File {file_id}: {filename}
        Summary: {summary}
        
        If the file needs to be renamed, suggest a new name.
        Reply with ONLY the new name, no explanation.
        If no renaming is needed, reply with the original filename.

        Examples of new names:
        - Invoice_2023.pdf
        - Annual_Report_2022.docx
        - Marketing_Image_01.jpg
        - Personal_Document.txt
        """
        
        try:
            response = chat.send_message(path_prompt)
            suggested_path = response.text.strip()
            
            print(f"Suggested path for file {file_id}: {suggested_path}")
            # Validate and sanitize the path
            valid_path, sanitized_path = validate_path(suggested_path)
            
            if valid_path:
                paths[file_id] = sanitized_path
            else:
                raise ValueError(f"Invalid path generated for file {file_id}: {suggested_path}. Using fallback path.")

            # Now handle renaming
            response = chat.send_message(file_rename_prompt)
            new_names[file_id] = response.text.strip()
            
                    
        except Exception as e:
            paths[file_id] = "Unorganized" + original_path
            new_names[file_id] = filename
            print(f"Error processing file {file_id}: {e}. Using fallback path and name.")
    
    return paths, new_names


def validate_path(path: str) -> Tuple[bool, str]:
    """
    Validate if the generated path is safe and usable.

    """
    # Remove any leading/trailing whitespaces
    path = path.strip()
    
    # Check if path is empty
    if not path:
        return False, "Miscellaneous"
    
    # Check for absolute paths or path traversal attempts
    if os.path.isabs(path) or '..' in path or '~' in path:
        return False, "Miscellaneous"
    
    # Check for valid characters only
    # Only allow alphanumeric characters, spaces, underscores, hyphens, and forward slashes
    if not re.match(r'^[a-zA-Z0-9_\-/ ]+$', path):
        return False, "Miscellaneous"
    
    # Check path length
    if len(path) > 100:
        return False, "Miscellaneous"
    
    # Normalize path separators and remove redundant slashes
    sanitized_path = os.path.normpath(path)
    
    # Replace spaces with underscores for cleaner paths
    sanitized_path = sanitized_path.replace(' ', '_')
    
    return True, sanitized_path

def generate_mapping(input_json_path: str, output_json_path: str, api_key: str) -> None:
    """
    Reads the summaries JSON file, processes the summaries, and generates
    a mapping JSON file with new destination paths and names for each file.

    """
    with open(input_json_path, "r", encoding="utf-8") as f:
        summaries = json.load(f)

    # Generate paths using a continuous session
    paths, filenames = generate_paths_with_session(summaries, api_key)
    
    mapping = []
    for file_meta in summaries:
        file_id = file_meta.get("id")
        filename = file_meta.get("filename")
        
        if not file_id or not filename:
            print(f"Warning: Missing id or filename for entry: {file_meta}")
            continue
        
        # Get the generated path for this file
        new_path = paths.get(file_id, "Miscellaneous")
        new_name = filenames.get(file_id, filename)

        mapping.append({
            "id": file_id,
            "new_name": new_name,
            "new_path": new_path,
        })

    with open(output_json_path, "w", encoding="utf-8") as out:
        json.dump(mapping, out, ensure_ascii=False, indent=2)

    print(f"Mapping JSON written to {output_json_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a mapping JSON file for file reorganization."
    )
    parser.add_argument(
        "input_file",
        help="Path to the input JSON file from part1-2 (summaries)."
    )
    parser.add_argument(
        "output_file",
        help="Path to save the generated mapping JSON file."
    )
    parser.add_argument(
        "--api_key",
        help="Gemini API key. If not provided, will look for GEMINI_API_KEY environment variable.",
        default=os.getenv("GEMINI_API_KEY")
    )
    args = parser.parse_args()

    if not args.api_key:
        raise ValueError("Gemini API key must be provided either as a command-line argument or as the GEMINI_API_KEY environment variable.")

    generate_mapping(args.input_file, args.output_file, args.api_key)