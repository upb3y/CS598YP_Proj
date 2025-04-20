import json
import os

import google.generativeai as genai
from docx import Document
from dotenv import load_dotenv
from PIL import Image
from pypdf import PdfReader

load_dotenv()

# Configure the Gemini API key via environment variable
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-2.0-flash")

def summarize_text(content: str) -> str:
    prompt = "Can you analyze the provided file content and generate concise, meaningful summary of its content (around 30 to 50 words): "
    response = model.generate_content(contents=[prompt, content])
    return response.text

def extract_pdf_text(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def extract_docx_text(path: str) -> str:
    doc = Document(path)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)

def summarize_files(input_json_path: str, output_json_path: str, root_folder: str) -> None:
    """
    Read a JSON file containing a list of files with 'id' and 'path' fields,
    summarize each file's content and write out a new JSON with summaries.
    """
    with open(input_json_path, "r", encoding="utf-8") as f:
        files = json.load(f)

    summaries = []
    for file_meta in files:
        file_id = file_meta.get("id")
        rel_path = file_meta.get("path")
        if not rel_path or not isinstance(rel_path, str):
            print(f"Warning: missing or invalid path for id={file_id}, skipping.")
            continue

        # Resolve full path using root_folder if necessary
        full_path = rel_path if os.path.isabs(rel_path) else os.path.join(root_folder, rel_path)
        name = os.path.basename(full_path)

        if not os.path.exists(full_path):
            print(f"Warning: file not found: {full_path}, skipping summary.")
            content = ""
        else:
            ext = full_path.lower().split('.')[-1]
            if ext == 'pdf':
                content = extract_pdf_text(full_path)
            elif ext in ('docx',):
                content = extract_docx_text(full_path)
            elif ext in ('png', 'jpg', 'jpeg'):
                content = Image.open(full_path)
            else:
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as infile:
                        content = infile.read()
                except Exception:
                    content = ""

        summary_text = summarize_text(content) if content else "(Could not read file content)"

        summaries.append({
            "id": file_id,
            "path": rel_path,
            "filename": name,
            "summary": summary_text,
        })

    with open(output_json_path, "w", encoding="utf-8") as out:
        json.dump(summaries, out, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=
        "Summarize files using Gemini LLM: specify input JSON and root folder, outputs to current dir"
    )
    parser.add_argument(
        "input_file",
        help="Path to JSON file listing files with 'id' and paths (relative or absolute)."
    )
    parser.add_argument(
        "root_folder",
        help="Path to the base folder where files are located."
    )
    args = parser.parse_args()

    input_path  = args.input_file
    root_folder = args.root_folder
    base_name   = os.path.splitext(os.path.basename(input_path))[0]
    output_path = f"{base_name}_summaries.json"

    summarize_files(input_path, output_path, root_folder)
    print(f"Summaries written to {output_path}")