# File Organization Pipeline

This project is a pipeline for organizing files based on their content and structure. It consists of four main steps:

1. **File Structure Retrieval**: Scans a directory and generates a JSON file with the structure of the files.
2. **Content Summarization**: Summarizes the content of the files using a generative AI model.
3. **File Organization Mapping**: Suggests new folder paths and names for the files based on their summaries.
4. **File Moving**: Moves and renames the files according to the generated mapping.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the environment variables:
   - Create a `.env` file in the root directory.
   - Add your Google API key for the generative AI model:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

## How to Run

1. Run the main pipeline:
   ```bash
   python main.py <root_folder> <output_folder>
   ```
   - `<root_folder>`: The directory containing the files to be organized.
   - `<output_folder>`: The directory where the organized files will be stored.

2. Example:
   ```bash
   python main.py test_folder test_moved
   ```

## Project Structure

- `main.py`: The entry point for running the entire pipeline.
- `part1_structure_retreiver.py`: Retrieves the file structure and generates a JSON file.
- `part1_2_content_summary.py`: Summarizes the content of the files.
- `part2_organizer.py`: Generates a mapping for organizing the files.
- `part3_file_mover.py`: Moves and renames the files based on the mapping.
- `test_part3_file_mover.py`: Unit tests for the file mover script.
- `requirements.txt`: Lists the dependencies required for the project.

## Notes

- Ensure that the Google API key is valid and has access to the generative AI model.
- The pipeline assumes that the input files are accessible and readable.
- Use the `--dry-run` option in `part3_file_mover.py` to preview the file moving operations without making changes.

