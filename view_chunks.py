import pandas as pd
import os

PARQUET_FILE = "processed_chunks.parquet" 

def view_chunks():
    """
    Reads the processed chunks from a Parquet file and displays them.
    """
    try:
        # Check if the Parquet file exists
        if not os.path.exists(PARQUET_FILE):
            print(f"Error: The file {PARQUET_FILE} does not exist.")
            return
        
        # Load the Parquet file into a DataFrame
        df = pd.read_parquet(PARQUET_FILE)
        
        # Display the first few rows of the DataFrame
        print("Displaying the first few chunks from the dataset:")
        print(df.head())
        
    except Exception as e:
        print(f"An error occurred while reading the Parquet file: {e}")

def main():
    """
    Main function to execute the view_chunks functionality.
    """
    print("Starting to view processed chunks...")
    view_chunks()

if __name__ == "__main__":
    main()
    print("Finished viewing chunks.")