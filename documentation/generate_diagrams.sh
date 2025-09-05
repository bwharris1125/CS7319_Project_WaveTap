#!/bin/bash

# Directory containing Mermaid diagrams
diagrams_dir="$(dirname "$0")/diagrams"
output_dir="$(dirname "$0")/diagrams_output"

# Ensure the output directory exists
mkdir -p "$output_dir"

# Try to find a system Chrome/Chromium and point puppeteer (used by mermaid-cli)
# at the executable so it doesn't try to use a downloaded browser.
detect_chrome() {
    # If user already set it, respect it
    if [ -n "$PUPPETEER_EXECUTABLE_PATH" ]; then
        echo "Using PUPPETEER_EXECUTABLE_PATH=$PUPPETEER_EXECUTABLE_PATH"
        return 0
    fi

    candidates=(
        "/usr/bin/google-chrome-stable"
        "/usr/bin/google-chrome"
        "/usr/bin/chromium"
        "/usr/bin/chromium-browser"
        "$(which google-chrome 2>/dev/null)"
        "$(which chromium 2>/dev/null)"
        "$(which chromium-browser 2>/dev/null)"
    )

    for c in "${candidates[@]}"; do
        if [ -n "$c" ] && [ -x "$c" ]; then
            export PUPPETEER_EXECUTABLE_PATH="$c"
            echo "Found browser executable: $c -> set PUPPETEER_EXECUTABLE_PATH"
            return 0
        fi
    done
}

detect_chrome

# Generate PNG files for each Mermaid diagram
for file in "$diagrams_dir"/*.mmd; do
    if [ -f "$file" ]; then
        output_file="$output_dir/$(basename "${file%.mmd}.png")"
        echo "Generating $output_file from $file"
        mmdc -i "$file" -o "$output_file"
    fi
done

echo "All diagrams have been processed. Output directory: $output_dir"
