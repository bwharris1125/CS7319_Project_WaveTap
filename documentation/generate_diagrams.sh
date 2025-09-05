#!/bin/bash

# Directory containing Mermaid diagrams
diagrams_dir="$(dirname "$0")/diagrams"
output_dir="$(dirname "$0")/diagrams/img_output"

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

# Default rendering size (landscape-preferred). Can be overridden by env vars:
# MMDC_WIDTH, MMDC_HEIGHT, MMDC_SCALE
MMDC_WIDTH=1400
MMDC_HEIGHT=800
MMDC_SCALE=1

# Generate PNG files for each Mermaid diagram
for file in "$diagrams_dir"/*.mmd; do
    if [ -f "$file" ]; then
        output_file="$output_dir/$(basename "${file%.mmd}.png")"
        echo "Generating $output_file from $file (width=${MMDC_WIDTH}, height=${MMDC_HEIGHT}, scale=${MMDC_SCALE})"
        mmdc -i "$file" -o "$output_file" -w "$MMDC_WIDTH" -H "$MMDC_HEIGHT" -s "$MMDC_SCALE"
    fi
done

echo "All diagrams have been processed. Output directory: $output_dir"
