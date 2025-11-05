import re
import os
import sys

def convert_to_dist(source_content):
    """
    Converts a "source" homework markdown file to a "distribution" version.
    
    Based on the provided example and user correction, this function:
    1. Removes all '提示' (Hint) and '说明' (Note) blocks.
    2. Adjusts Markdown heading levels for questions:
       - All "1.", "2." etc. items -> H3 (###)
       - All "- (1)", "- (2)" etc. sub-items -> H4 (####)
    """
    
    # 1. Remove Hint/说明 blocks
    # This regex finds a line starting with '提示' or '说明', 
    # matches all content (including newlines) non-greedily,
    # and stops *before* (using a lookahead ?=) a new line that 
    # starts with a new problem (e.g., "1. ", "- (", "##") or the end of the file.
    pattern = r"^\s*(\*\*提示\*\*：|\*\*说明\*\*：)[\s\S]*?(?=(?:^\s*(?:\d+\. |-\s*\(|##))|$(?![\s\S]))"
    
    # Remove the matched blocks
    content_no_hints = re.sub(pattern, "", source_content, flags=re.MULTILINE)
    
    # Clean up extra blank lines that may be left after removal
    content_cleaned = re.sub(r"\n{3,}", "\n\n", content_no_hints)

    # 2. Adjust Headings
    output_lines = []
    
    for line in content_cleaned.splitlines():
        
        # Make a copy to transform
        transformed_line = line
        
        # Check for sub-items first, e.g., "- (1)" -> "#### (1)"
        if re.match(r"^\s*-\s*\((.*?)\)", line):
            transformed_line = re.sub(r"^\s*-\s*\((.*?)\)(.*)", r"#### (\1)\2", line)
        
        # Check for top-level items, e.g., "1." -> "### 1."
        # This now applies to ALL sections per user request.
        elif re.match(r"^\s*(\d+)\.", line):
            transformed_line = re.sub(r"^\s*(\d+)\.", r"### \1.", line)
        
        output_lines.append(transformed_line)
            
    return "\n".join(output_lines)

def main():
    """
    Main function to read a source markdown file from command-line arguments,
    convert it, and write to a new output file.
    """
    
    # 1. Check for command-line argument
    if len(sys.argv) < 2:
        print(f"\n[Error] No input file provided.")
        print(f"Usage: python {os.path.basename(sys.argv[0])} <path_to_source_file.md>")
        sys.exit(1) # Exit with an error code

    source_filepath = sys.argv[1]

    # 2. Check if the file exists
    if not os.path.isfile(source_filepath):
        print(f"\n[Error] File not found: '{source_filepath}'")
        sys.exit(1)
        
    # 3. Determine output path
    try:
        # Get the full, absolute path to be safe
        source_filepath_abs = os.path.abspath(source_filepath)
        # Get the directory where the source file is located
        source_dir = os.path.dirname(source_filepath_abs)
        # Get the filename (e.g., "source.md")
        source_filename_full = os.path.basename(source_filepath_abs)
        # Split the filename into base and extension (e.g., "source" and ".md")
        source_filename_base, source_ext = os.path.splitext(source_filename_full)
        
        # Create the new output filename (e.g., "source_out.md")
        output_filename = f"{source_filename_base}_out.md"
        # Join the directory and new filename to get the full output path
        output_filepath = os.path.join(source_dir, output_filename)
        
    except Exception as e:
        print(f"\n[Error] Could not determine output path: {e}")
        sys.exit(1)

    # 4. Process the file
    try:
        # Read the source file
        with open(source_filepath_abs, "r", encoding="utf-8") as f:
            source_content = f.read()
        
        print(f"Reading '{source_filepath_abs}'...")
        
        # Perform the conversion
        dist_content = convert_to_dist(source_content)
        
        # Write the new content to the destination file
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(dist_content)
            
        print(f"Successfully converted content and saved to '{output_filepath}'.")
        print("\n--- Transformation Summary ---")
        print("1. Removed all '**提示**：' (Hint) blocks.")
        print("2. Removed all '**说明**：' (Note) blocks.")
        print("3. Adjusted all '1.' type questions to H3 (###).")
        print("4. Adjusted all '- (1)' type sub-questions to H4 (####).")

    except Exception as e:
        print(f"\n[Error] An unexpected error occurred during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()