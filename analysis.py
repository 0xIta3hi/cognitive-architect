import os
import json
import pandas as pd
from collections import Counter
from pathlib import Path
from tqdm import tqdm
import pypdf
import nltk
from nltk.corpus import stopwords

# --- Configuration ---
DATASET_PATH = "./final_train"
# --- End Configuration ---


def analyze_file_content(file_path):
    """
    Analyzes the content of a single file to get its word count.
    Returns word count, or 0 if the file can't be read or is empty.
    """
    try:
        ext = file_path.suffix.lower()
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return len(content.split())
        elif ext == '.pdf':
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
            return len(text.split())
        elif ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # A simple way to estimate text content in a JSON file
            return len(json.dumps(data).split())
        else:
            return 0
    except Exception as e:
        # This will catch errors from corrupted files, etc.
        # print(f"Could not process {file_path}: {e}")
        return 0

def load_and_chunk_document(file_path):
    try:
        ext = file_path.suffix.lower()
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content.split('\n\n')  # Chunk by paragraphs
        elif ext == '.json':
            with open(file_path, 'r', encoding="utf-8") as f:
                data = json.load(f)
            
            title = data.get('metadata,', {}).get('title', '')
            abstract_parts = [p.get('text', '') for p in data.get('abstract', [])]
            body_parts = [p.get('text', '') for p in data.get('body', [])]
            full_text = f"Title: {title}\n Abstract: {' '.join(abstract_parts)}\n Body: {' '.join(body_parts)}"
        else:
            return []
    except Exception as e:
        print(f"Error loading or chunking document {file_path}: {e}")
        return []
        

def main():
    """
    Main function to walk through the dataset and perform analysis.
    """
    print(f"Starting analysis of dataset at: {DATASET_PATH}\n")
    
    # Check if the path exists
    if not os.path.isdir(DATASET_PATH):
        print(f"Error: Directory not found at {DATASET_PATH}")
        print("Please update the DATASET_PATH variable in the script.")
        return

    # First, get a list of all file paths to use with tqdm
    all_files = [Path(os.path.join(root, file))
                 for root, _, files in os.walk(DATASET_PATH)
                 for file in files]

    if not all_files:
        print("No files found in the specified directory.")
        return

    # --- Data Collection ---
    file_stats = []
    file_type_counts = Counter()

    for file_path in tqdm(all_files, desc="Analyzing files"):
        file_size = os.path.getsize(file_path)
        file_type = file_path.suffix.lower()
        file_type_counts[file_type] += 1
        
        word_count = analyze_file_content(file_path)
        
        file_stats.append({
            'path': file_path,
            'type': file_type,
            'size_bytes': file_size,
            'word_count': word_count
        })

    # --- Reporting ---
    print("\n--- Dataset Analysis Report ---\n")
    
    # Convert stats to a pandas DataFrame for easy analysis
    df = pd.DataFrame(file_stats)
    
    # 1. Overall Stats
    total_files = len(df)
    total_size_gb = df['size_bytes'].sum() / (1024**3)
    print("## Overall Statistics")
    print(f"Total number of files: {total_files:,}")
    print(f"Total dataset size: {total_size_gb:.2f} GB")
    print("-" * 30)

    # 2. File Type Distribution
    print("## File Type Distribution")
    type_df = pd.DataFrame(file_type_counts.most_common(), columns=['File Type', 'Count'])
    print(type_df.to_string(index=False))
    print("-" * 30)

    # 3. File Size Analysis
    print("## File Size Analysis")
    # Convert bytes to MB for readability
    df['size_mb'] = df['size_bytes'] / (1024**2)
    print(f"Average file size: {df['size_mb'].mean():.4f} MB")
    print(f"Smallest file size: {df['size_mb'].min():.4f} MB")
    print(f"Largest file size: {df['size_mb'].max():.2f} MB")
    print("-" * 30)

    # 4. Content Analysis (Word Count)
    print("## Content Analysis (Word Count)")
    # Filter out files where word count could not be determined
    countable_files = df[df['word_count'] > 0]
    print(f"Average word count (for readable files): {countable_files['word_count'].mean():.0f}")
    print(f"Min word count: {countable_files['word_count'].min():.0f}")
    print(f"Max word count: {countable_files['word_count'].max():,}")
    print("-" * 30)
    
    # 5. Sample Vocabulary Analysis
    print("## Sample Vocabulary Analysis")
    print("Analyzing a sample text file for common terms (excluding stopwords)...")
    try:
        # Find the first text file to analyze
        sample_txt_file = df[df['type'] == '.txt'].iloc[0]['path']
        nltk.download('stopwords', quiet=True)
        stop_words = set(stopwords.words('english'))
        
        with open(sample_txt_file, 'r', encoding='utf-8') as f:
            content = f.read().lower() # Lowercase for consistency
        
        words = [word for word in content.split() if word.isalpha() and word not in stop_words]
        common_words = Counter(words).most_common(15)
        
        print(f"\nTop 15 most common words in '{sample_txt_file.name}':")
        common_df = pd.DataFrame(common_words, columns=['Word', 'Frequency'])
        print(common_df.to_string(index=False))
    except (IndexError, FileNotFoundError):
        print("No sample .txt file found to perform vocabulary analysis.")
    except Exception as e:
        print(f"Could not perform vocabulary analysis: {e}")
    print("\n--- End of Report ---")

if __name__ == "__main__":
    main()