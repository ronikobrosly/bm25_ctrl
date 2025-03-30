#!/usr/bin/env python3
"""
Control Mapping Pipeline for Cloud Services
This pipeline maps cloud services to control policies using BM25 retrieval.
"""

import os
import json
import csv
import re
import nltk
import pandas as pd
from tqdm import tqdm
from rank_bm25 import BM25Okapi
from pypdf import PdfReader
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from typing import Dict, List, Tuple, Any, Optional

# Download required NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class ControlMapper:
    """Maps cloud services to control policies using BM25 retrieval."""
    
    def __init__(self, controls_csv_path: str):
        """Initialize the ControlMapper with control policies.
        
        Args:
            controls_csv_path: Path to CSV file containing control policies
        """
        self.controls = self._load_controls(controls_csv_path)
        self.tokenized_controls = [self._preprocess_text(ctrl) for ctrl in self.controls]
        self.bm25 = BM25Okapi(self.tokenized_controls)
        
    def _load_controls(self, csv_path: str) -> List[Dict[str, Any]]:
        """Load control policies from CSV.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of control dictionaries with id and description
        """
        controls = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) > 1:  # Ensure we have at least 2 columns
                    try:
                        # First column is control ID, second column is description
                        control_id = int(row[0])
                        controls.append({
                            'id': control_id,
                            'description': row[1].strip()
                        })
                    except (ValueError, IndexError):
                        # Skip rows that don't have a valid integer ID
                        continue
        return controls
    
    def _preprocess_text(self, text_dict: Dict[str, Any]) -> List[str]:
        """Preprocess text for BM25 indexing.
        
        Args:
            text_dict: Dictionary containing text to preprocess
            
        Returns:
            List of tokens
        """
        text = text_dict.get('description', '')
        if not text:
            return []
            
        # Tokenize and remove stopwords
        tokens = word_tokenize(text.lower())
        stop_words = set(stopwords.words('english'))
        return [token for token in tokens if token.isalnum() and token not in stop_words]
    
    def extract_security_section(self, pdf_path: str) -> str:
        """Extract security-related sections from cloud service documentation.
        
        Args:
            pdf_path: Path to PDF documentation
            
        Returns:
            String containing security-related content
        """
        reader = PdfReader(pdf_path)
        full_text = ""
        security_text = ""
        
        # Extract all text from PDF
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        
        # Look for security section
        security_patterns = [
            r'(?i)security[^\n.]*(?:\n|.){1,5000}',
            r'(?i)compliance[^\n.]*(?:\n|.){1,3000}',
            r'(?i)data protection[^\n.]*(?:\n|.){1,3000}',
            r'(?i)authentication[^\n.]*(?:\n|.){1,2000}',
            r'(?i)authorization[^\n.]*(?:\n|.){1,2000}',
            r'(?i)encryption[^\n.]*(?:\n|.){1,2000}'
        ]
        
        for pattern in security_patterns:
            matches = re.finditer(pattern, full_text)
            for match in matches:
                security_text += match.group(0) + "\n\n"
        
        # If no security section found, use a chunk of the full text
        if not security_text and full_text:
            # Limit to 8000 tokens (approximate)
            security_text = full_text[:40000]
            
        return security_text
    
    def map_controls(
        self, 
        service_name: str, 
        doc_pdf_path: str, 
        analyst_note: str, 
        top_n: int = 10
    ) -> Dict[str, Dict[str, str]]:
        """Map cloud service to control policies.
        
        Args:
            service_name: Name of the cloud service
            doc_pdf_path: Path to service documentation PDF
            analyst_note: Analyst's note about service
            top_n: Number of top controls to consider
            
        Returns:
            Dictionary mapping service to controls with confidence levels
        """
        # Extract security section from PDF
        security_text = self.extract_security_section(doc_pdf_path)
        
        # Combine security text with analyst note for query
        query_text = f"{service_name} {analyst_note} {security_text[:5000]}"
        query_tokens = self._preprocess_text({'description': query_text})
        
        # Get BM25 scores for controls
        scores = self.bm25.get_scores(query_tokens)
        
        # Normalize scores to determine confidence levels
        max_score = max(scores) if scores else 1.0
        norm_scores = [score / max_score for score in scores]
        
        # Create sorted list of (control_id, score) tuples
        scored_controls = list(zip(range(len(self.controls)), norm_scores))
        scored_controls.sort(key=lambda x: x[1], reverse=True)
        
        # Get top N controls
        top_controls = scored_controls[:top_n]
        
        # Assign confidence levels based on normalized scores
        result = {}
        for control_id, score in top_controls:
            if score > 0.7:
                confidence = "high"
            elif score > 0.4:
                confidence = "medium"
            else:
                confidence = "low"
                
            if control_id not in result:
                result[control_id] = confidence
                
        # Format the output
        return {service_name: result}
    
    def get_control_description(self, control_id: int) -> str:
        """Get description of a control by ID.
        
        Args:
            control_id: ID of the control
            
        Returns:
            Control description
        """
        if 0 <= control_id < len(self.controls):
            return self.controls[control_id]['description']
        return "Control not found"

def main():
    """Main function to demonstrate the pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Map cloud services to control policies')
    parser.add_argument('--controls', required=True, help='Path to controls CSV file')
    parser.add_argument('--service', required=True, help='Name of cloud service')
    parser.add_argument('--doc', required=True, help='Path to service documentation PDF')
    parser.add_argument('--note', required=True, help='Analyst note about the service')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--top_n', type=int, default=10, help='Number of top controls to consider')
    
    args = parser.parse_args()
    
    # Initialize control mapper
    mapper = ControlMapper(args.controls)
    
    # Map controls for service
    result = mapper.map_controls(args.service, args.doc, args.note, args.top_n)
    
    # Print results
    print(json.dumps(result, indent=2))
    
    # Save results to file if output path provided
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
            
if __name__ == '__main__':
    main() 