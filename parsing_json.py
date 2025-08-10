import json
import os
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Configuration ---
# This path should point to the root directory of your unzipped dataset.
DATASET_PATH = "./final_train" 
# This will be the name of your final, processed output file.
OUTPUT_FILENAME = "processed_chunks.parquet"
# --- End Configuration ---

def parse_json_to_prose(file_path):
    """
    Reads a JSON file with a specific structure, extracts key information,
    and formats it into a clean, natural language string.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # --- Extracting all the fields from the JSON data ---
        # Using .get() with a default value is safer.
        category = data.get('category')
        search_results = data.get('search_results', [])
        air_date = data.get('air_date')
        question = data.get('question')
        value = data.get('value')
        answer = data.get('answer')
        round_info = data.get('round') # Renamed to avoid conflict with round() function
        show_number = data.get('show_number')

        prose_parts = []

        # --- FIX: Correctly check if the field exists and has a value ---
        if category:
            prose_parts.append(f"The category is: {category}.")
        if air_date:
            prose_parts.append(f"The air date is: {air_date}.")
        if question:
            prose_parts.append(f"The question is: {question}.")
        if value:
            prose_parts.append(f"The value is: {value}.")
        if answer:
            prose_parts.append(f"The answer is: {answer}.")
        if round_info:
            prose_parts.append(f"The round is: {round_info}.")
        if show_number:
            prose_parts.append(f"The show number is: {show_number}.")

        # Process the list of search results
        if search_results:
            results_text_parts = []
            for result in search_results:
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                # Only add if there's actual content
                if title or snippet:
                    results_text_parts.append(f"Title: {title}. Snippet: {snippet}.")
            if results_text_parts:
                prose_parts.append("Relevant search results include: " + " ".join(results_text_parts))
        
        return " ".join(prose_parts)

    except Exception as e:
        # print(f"Warning: Could not process JSON file {file_path}. Reason: {e}")
        return ""

def parse_txt_file(file_path):
    """Reads a plain text file and returns its content as a string."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        # print(f"Warning: Could not process TXT file {file_path}. Reason: {e}")
        return ""

def main():
    """
    Main function to discover all files, process them based on type,
    chunk the content, and save everything to a single Parquet file.
    """
    dataset_path = Path(DATASET_PATH)
    if not dataset_path.is_dir():
        print(f"Error: Dataset path '{DATASET_PATH}' is not a valid directory.")
        return

    # Use .rglob to find all files recursively in all subdirectories
    all_files = list(dataset_path.rglob('*.*'))
    print(f"Found {len(all_files)} files to process.")

    # Instantiate our text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        length_function=len
    )

    processed_data = []
    
    # Use tqdm for a nice progress bar
    for file_path in tqdm(all_files, desc="Processing files"):
        prose = ""
        ext = file_path.suffix.lower()

        if ext == '.json':
            prose = parse_json_to_prose(file_path)
        elif ext == '.txt':
            prose = parse_txt_file(file_path)

        # If we got valid text, chunk it and add it to our list
        if prose:
            chunks = text_splitter.split_text(prose)
            for i, chunk in enumerate(chunks):
                processed_data.append({
                    'source_file': str(file_path.name), # Store only the filename
                    'chunk_id': f"{file_path.stem}_{i}",
                    'chunk_text': chunk
                })

    if not processed_data:
        print("No data was processed. Please check your dataset and file paths.")
        return
        
    print(f"\nSuccessfully processed {len(all_files)} files into {len(processed_data)} chunks.")

    # Create a pandas DataFrame and save to Parquet
    print("Saving chunks to Parquet file...")
    df = pd.DataFrame(processed_data)
    df.to_parquet(OUTPUT_FILENAME, index=False)
    
    print(f"All done! Your processed data is saved to '{OUTPUT_FILENAME}'")

if __name__ == "__main__":
    main()