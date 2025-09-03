#!/bin/bash

# Directory containing Mermaid diagrams
diagrams_dir="$(dirname "$0")/diagrams"
output_dir="$(dirname "$0")/diagrams_output"

# Ensure the output directory exists
mkdir -p "$output_dir"

# Generate PNG files for each Mermaid diagram
for file in "$diagrams_dir"/*.mmd; do
    if [ -f "$file" ]; then
        output_file="$output_dir/$(basename "${file%.mmd}.png")"
        echo "Generating $output_file from $file"
        mmdc -i "$file" -o "$output_file"
    fi
done

echo "All diagrams have been processed. Output directory: $output_dir"
