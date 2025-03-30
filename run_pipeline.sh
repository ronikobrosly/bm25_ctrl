#!/bin/bash
# Run the entire control mapping pipeline

# Create necessary directories
mkdir -p data
mkdir -p output

# Default values
CONTROLS_FILE="data/controls.csv"
SERVICE_NAME="AWS Timestream"
DOC_FILE="data/timestream_security.pdf"
ANALYST_NOTE="A threat agent misconfigured inbound connection settings, accept lists, and/or VPC firewall rules, allowing them to bypass security controls and gain unauthorized access to sensitive resources and APIs, leading to the theft or disclosure of highly confidential data"
OUTPUT_DIR="output"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --controls)
            CONTROLS_FILE="$2"
            shift 2
            ;;
        --service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --doc)
            DOC_FILE="$2"
            shift 2
            ;;
        --note)
            ANALYST_NOTE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if the doc file is a text file rather than PDF
if [[ "$DOC_FILE" == *.txt ]]; then
    echo "Converting text file to PDF..."
    PDF_FILE="${DOC_FILE%.txt}.pdf"
    python create_test_pdf.py --input "$DOC_FILE" --output "$PDF_FILE"
    DOC_FILE="$PDF_FILE"
fi

# Run the control mapping
echo "Running control mapping pipeline..."
python demo.py --controls "$CONTROLS_FILE" --service "$SERVICE_NAME" --doc "$DOC_FILE" --note "$ANALYST_NOTE"

# Run LLM-enhanced mapping if available
if [[ -f "llm_enhanced_mapping.py" ]]; then
    echo "Running LLM-enhanced mapping..."
    python llm_enhanced_mapping.py --controls "$CONTROLS_FILE" --service "$SERVICE_NAME" --doc "$DOC_FILE" --note "$ANALYST_NOTE" --output "${OUTPUT_DIR}/${SERVICE_NAME// /_}_enhanced.json"
fi

echo "Pipeline completed successfully!"
echo "Results available in: ${OUTPUT_DIR}" 