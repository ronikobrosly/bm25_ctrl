"""
Unified Control Mapping Pipeline
Combines BM25 retrieval and LLM enhancement in a single pipeline.
Supports extraction of specific page ranges from PDFs.
"""

import os
import json
import argparse
import tempfile
from ctrl_mapping import ControlMapper
from llm_enhanced_mapping import LLMEnhancedMapper
from pypdf import PdfReader, PdfWriter

def extract_pdf_pages(input_pdf_path, start_page=None, end_page=None):
    """
    Extracts a specific page range from a PDF and returns a temporary file path.
    If no page range is specified, returns the original PDF path.
    
    Args:
        input_pdf_path: Path to the input PDF file
        start_page: First page to extract (1-indexed, optional)
        end_page: Last page to extract (1-indexed, inclusive, optional)
        
    Returns:
        Path to the extracted PDF (or original if no extraction was done)
    """
    # If no page range specified, return the original PDF path
    if start_page is None and end_page is None:
        return input_pdf_path
    
    # Validate PDF path
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"PDF file not found: {input_pdf_path}")
    
    try:
        with open(input_pdf_path, "rb") as input_file:
            reader = PdfReader(input_file)
            total_pages = len(reader.pages)
            
            # Validate page range
            if start_page is None:
                start_page = 1
            if end_page is None:
                end_page = total_pages
                
            # Convert to 0-based index and ensure within bounds
            start_idx = max(0, min(start_page - 1, total_pages - 1))
            end_idx = max(start_idx, min(end_page - 1, total_pages - 1))
            
            # Create a temporary output file
            temp_output = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_output_path = temp_output.name
            temp_output.close()
            
            # Extract the specified pages
            writer = PdfWriter()
            for page_num in range(start_idx, end_idx + 1):
                writer.add_page(reader.pages[page_num])
            
            with open(temp_output_path, "wb") as output_file:
                writer.write(output_file)
                
            print(f"Extracted pages {start_page}-{end_page} from PDF ({end_idx - start_idx + 1} pages total)")
            return temp_output_path
            
    except Exception as e:
        print(f"Error extracting PDF pages: {e}")
        return input_pdf_path  # Fall back to original PDF

def run_unified_pipeline(
    controls_file: str,
    service_name: str,
    doc_file: str,
    analyst_note: str,
    output_file: str = None,
    top_n_bm25: int = 10,
    top_n_llm: int = 5,
    llm_endpoint: str = None,
    start_page: int = None,
    end_page: int = None
):
    """
    Run the complete pipeline with BM25 retrieval followed by LLM enhancement.
    
    Args:
        controls_file: Path to CSV file with control policies
        service_name: Name of the cloud service
        doc_file: Path to service documentation PDF
        analyst_note: Analyst's note about potential threats
        output_file: Path to save results (optional)
        top_n_bm25: Number of controls to retrieve with BM25
        top_n_llm: Number of controls to enhance with LLM
        llm_endpoint: Endpoint URL for LLM API (optional)
        start_page: First page to analyze (1-indexed, optional)
        end_page: Last page to analyze (1-indexed, inclusive, optional)
    
    Returns:
        Dictionary with final control mappings
    """
    print(f"\n1. Initializing pipeline for {service_name}...")
    
    # Extract relevant pages from PDF if needed
    if doc_file.lower().endswith('.pdf') and (start_page is not None or end_page is not None):
        print(f"   Extracting pages {start_page or 1} to {end_page or 'end'} from document...")
        processed_doc = extract_pdf_pages(doc_file, start_page, end_page)
        
        # If a temporary file was created, use it and ensure cleanup
        if processed_doc != doc_file:
            temp_file_created = True
            doc_file = processed_doc
        else:
            temp_file_created = False
    else:
        temp_file_created = False
    
    try:
        # Initialize the BM25 control mapper
        base_mapper = ControlMapper(controls_file)
        print(f"   Loaded {len(base_mapper.controls)} control policies")
        
        # Stage 1: BM25 retrieval
        print("\n2. Running BM25 retrieval to identify candidate controls...")
        bm25_results = base_mapper.map_controls(
            service_name, 
            doc_file, 
            analyst_note,
            top_n=top_n_bm25
        )
        print(f"   Identified {len(bm25_results.get(service_name, {}))} potential control matches")
        
        # Stage 2: LLM enhancement
        print("\n3. Enhancing top controls with LLM analysis...")
        llm_mapper = LLMEnhancedMapper(base_mapper, llm_endpoint)
        enhanced_results = llm_mapper.enhance_control_mapping(
            service_name,
            doc_file,
            analyst_note,
            bm25_results,
            max_enhanced_controls=top_n_llm
        )
        
        # Format and combine the final results
        final_results = {
            service_name: {}
        }
        
        print("\n4. Building final control mappings with justifications...")
        
        # Get enhanced control results
        enhanced_controls = enhanced_results.get(service_name, {})
        
        # Process all BM25 results
        for control_id_str, confidence in bm25_results.get(service_name, {}).items():
            control_id = int(control_id_str)
            control_desc = base_mapper.get_control_description(control_id)
            
            # Check if this control was enhanced by LLM
            if control_id_str in enhanced_controls:
                enhanced_data = enhanced_controls[control_id_str]
                
                # Use LLM confidence if available, otherwise use BM25 confidence
                final_results[service_name][control_id_str] = {
                    "confidence": enhanced_data.get("llm_confidence", confidence),
                    "applicable": enhanced_data.get("llm_applicable", True),
                    "description": control_desc,
                    "justification": enhanced_data.get("justification", "Based on BM25 retrieval score")
                }
            else:
                # Include BM25-only result
                final_results[service_name][control_id_str] = {
                    "confidence": confidence,
                    "applicable": True,  # Assume applicable by default
                    "description": control_desc,
                    "justification": "Based on BM25 retrieval score"
                }
        
        # Save results if output file provided
        if output_file:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(final_results, f, indent=2)
            print(f"\n5. Results saved to: {output_file}")
        
        # Generate simple version of results for easy reference
        simple_results = {
            service_name: {
                ctrl_id: ctrl_data["confidence"] 
                for ctrl_id, ctrl_data in final_results[service_name].items()
                if ctrl_data.get("applicable", True)  # Only include applicable controls
            }
        }
        
        # Print summary of results
        print("\nCONTROL MAPPING SUMMARY:")
        print("-" * 80)
        print(f"Cloud Service: {service_name}")
        print(f"Total controls analyzed: {len(base_mapper.controls)}")
        print(f"Controls matched by BM25: {len(bm25_results.get(service_name, {}))}")
        print(f"Controls enhanced by LLM: {len(enhanced_controls)}")
        print(f"Final applicable controls: {len(simple_results.get(service_name, {}))}")
        print("-" * 80)
        print("\nTOP CONTROL MATCHES:")
        
        # Print top 5 control matches
        sorted_controls = sorted(
            [(int(cid), final_results[service_name][cid]) for cid in final_results[service_name]],
            key=lambda x: {"high": 0, "medium": 1, "low": 2}[x[1]["confidence"]]
        )
        
        for control_id, control_data in sorted_controls[:5]:
            print(f"\nControl {control_id}: {control_data['description']}")
            print(f"  Confidence: {control_data['confidence'].upper()}")
            print(f"  Justification: {control_data['justification']}")
        
        # Return both detailed and simple results
        return {
            "detailed": final_results,
            "simple": simple_results
        }
    
    finally:
        # Clean up temporary file if created
        if temp_file_created and os.path.exists(doc_file):
            try:
                os.unlink(doc_file)
                print("   Temporary file cleanup completed")
            except Exception as e:
                print(f"   Warning: Failed to clean up temporary file: {e}")

def main():
    """Main entry point for the unified pipeline."""
    parser = argparse.ArgumentParser(description="Unified Control Mapping Pipeline")
    parser.add_argument("--controls", required=True, help="Path to controls CSV file")
    parser.add_argument("--service", required=True, help="Name of cloud service")
    parser.add_argument("--doc", required=True, help="Path to service documentation PDF")
    parser.add_argument("--note", required=True, help="Analyst note about the service")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--bm25-top", type=int, default=10, help="Number of top controls from BM25")
    parser.add_argument("--llm-top", type=int, default=5, help="Number of controls to enhance with LLM")
    parser.add_argument("--llm-endpoint", help="Endpoint URL for LLM API")
    parser.add_argument("--start-page", type=int, help="First page to analyze (1-indexed)")
    parser.add_argument("--end-page", type=int, help="Last page to analyze (1-indexed, inclusive)")
    
    args = parser.parse_args()
    
    # Run unified pipeline
    results = run_unified_pipeline(
        args.controls,
        args.service,
        args.doc,
        args.note,
        args.output,
        args.bm25_top,
        args.llm_top,
        args.llm_endpoint,
        args.start_page,
        args.end_page
    )
    
    # Print the simplified results for easy reference
    print("\nSIMPLIFIED RESULTS:")
    print(json.dumps(results["simple"], indent=2))

if __name__ == "__main__":
    main()