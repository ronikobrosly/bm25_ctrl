#!/usr/bin/env python3
"""
Utility script to convert a text file to PDF for testing purposes.
"""

import os
import argparse
from fpdf import FPDF

def create_pdf_from_text(text_file, output_pdf):
    """Convert a text file to PDF.
    
    Args:
        text_file: Path to input text file
        output_pdf: Path to output PDF file
    """
    # Check if input file exists
    if not os.path.exists(text_file):
        print(f"Error: Input file {text_file} does not exist.")
        return False
    
    # Create PDF object
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Set margins
    pdf.set_margins(10, 10, 10)
    
    # Read text file
    with open(text_file, "r", encoding="utf-8") as f:
        text = f.read()
    
    # Split text into lines
    lines = text.split("\n")
    
    # Add each line to PDF
    for line in lines:
        # Check if line contains bullet point
        if line.strip().startswith("•"):
            # Indent bullet points
            pdf.cell(5)
        
        # Add text
        pdf.multi_cell(0, 5, line)
    
    # Save PDF
    try:
        pdf.output(output_pdf)
        print(f"PDF created successfully: {output_pdf}")
        return True
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Convert text file to PDF")
    parser.add_argument("--input", required=True, help="Input text file")
    parser.add_argument("--output", required=True, help="Output PDF file")
    
    args = parser.parse_args()
    
    create_pdf_from_text(args.input, args.output)

if __name__ == "__main__":
    main() 