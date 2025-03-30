#!/usr/bin/env python3
"""
LLM-Enhanced Control Mapping for Cloud Services.
This module extends the base control mapping pipeline with LLM-powered enhancements.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from ctrl_mapping import ControlMapper

# Sample prompt template for LLM
LLM_PROMPT_TEMPLATE = """
You are a cybersecurity expert at a financial institution. Your task is to assess whether a cloud service needs to comply with specific security controls.

CLOUD SERVICE: {service_name}

SECURITY DOCUMENTATION EXCERPT:
{security_doc}

ANALYST CONCERN:
{analyst_note}

CONTROL POLICY:
{control_description}

Based solely on the information above, assess whether the cloud service should be subject to this control policy.
Provide a confidence level (HIGH, MEDIUM, or LOW) and a brief justification (2-3 sentences maximum).

Answer in JSON format:
{{
  "is_applicable": true/false,
  "confidence": "HIGH/MEDIUM/LOW",
  "justification": "Your brief justification here"
}}
"""

class LLMEnhancedMapper:
    """
    Extends the base ControlMapper with LLM-powered enhancements.
    This class uses Llama 3.1 70B for more accurate control mappings.
    """
    
    def __init__(self, base_mapper: ControlMapper, llm_endpoint: Optional[str] = None):
        """
        Initialize the LLM-enhanced mapper.
        
        Args:
            base_mapper: Base ControlMapper instance
            llm_endpoint: Endpoint URL for the LLM API
        """
        self.base_mapper = base_mapper
        self.llm_endpoint = llm_endpoint or os.environ.get("LLM_ENDPOINT", "")
        
    def get_llm_assessment(
        self, 
        service_name: str, 
        security_doc: str, 
        analyst_note: str, 
        control_description: str
    ) -> Dict[str, Any]:
        """
        Get LLM assessment for a control policy.
        
        Args:
            service_name: Name of the cloud service
            security_doc: Security documentation excerpt
            analyst_note: Analyst's note about service
            control_description: Description of the control policy
            
        Returns:
            Dictionary with LLM assessment
        """
        # In a real implementation, this would make an API call to the LLM endpoint
        # For this demo, we'll simulate the LLM response
        
        prompt = LLM_PROMPT_TEMPLATE.format(
            service_name=service_name,
            security_doc=security_doc[:2000],  # Truncate to fit context window
            analyst_note=analyst_note,
            control_description=control_description
        )
        
        # This would be replaced with actual LLM API call
        # For demo purposes, we'll simulate a response based on keywords
        time.sleep(0.5)  # Simulate API latency
        
        # Simple keyword matching for demo purposes
        keywords_in_control = control_description.lower().split()
        keywords_in_doc = security_doc.lower().split()
        common_words = set(keywords_in_control).intersection(set(keywords_in_doc))
        
        # Simulate LLM decision based on keyword overlap
        if len(common_words) > 5:
            return {
                "is_applicable": True,
                "confidence": "HIGH",
                "justification": "Strong keyword match between control and documentation."
            }
        elif len(common_words) > 2:
            return {
                "is_applicable": True,
                "confidence": "MEDIUM",
                "justification": "Moderate keyword match between control and documentation."
            }
        else:
            return {
                "is_applicable": False,
                "confidence": "LOW",
                "justification": "Minimal keyword match between control and documentation."
            }
    
    def enhance_control_mapping(
        self, 
        service_name: str, 
        doc_path: str, 
        analyst_note: str, 
        base_results: Dict[str, Dict[str, str]],
        max_enhanced_controls: int = 5
    ) -> Dict[str, Dict[str, Any]]:
        """
        Enhance control mapping with LLM assessments.
        
        Args:
            service_name: Name of the cloud service
            doc_path: Path to service documentation
            analyst_note: Analyst's note about service
            base_results: Results from base control mapper
            max_enhanced_controls: Maximum number of controls to enhance
            
        Returns:
            Enhanced control mapping results
        """
        # Extract security section
        security_doc = self.base_mapper.extract_security_section(doc_path)
        
        # Get controls from base results
        service_controls = base_results.get(service_name, {})
        
        # Sort controls by confidence
        sorted_controls = sorted(
            [(int(ctrl_id), conf) for ctrl_id, conf in service_controls.items()],
            key=lambda x: {"high": 0, "medium": 1, "low": 2}[x[1]]
        )
        
        # Select controls to enhance (prioritize high confidence ones)
        controls_to_enhance = sorted_controls[:max_enhanced_controls]
        
        # Enhance each selected control
        enhanced_results = {service_name: {}}
        for control_id, base_confidence in controls_to_enhance:
            # Get control description
            control_description = self.base_mapper.get_control_description(control_id)
            
            # Get LLM assessment
            llm_assessment = self.get_llm_assessment(
                service_name, 
                security_doc, 
                analyst_note, 
                control_description
            )
            
            # Add enhanced result
            enhanced_results[service_name][str(control_id)] = {
                "base_confidence": base_confidence,
                "llm_applicable": llm_assessment["is_applicable"],
                "llm_confidence": llm_assessment["confidence"].lower(),
                "justification": llm_assessment["justification"]
            }
        
        return enhanced_results

def main():
    """Main function to demonstrate LLM-enhanced mapping."""
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM-Enhanced Control Mapping")
    parser.add_argument("--controls", default="data/controls.csv", help="Path to controls CSV file")
    parser.add_argument("--service", default="AWS Timestream", help="Name of cloud service")
    parser.add_argument("--doc", default="data/timestream_security.pdf", help="Path to service documentation PDF")
    parser.add_argument("--note", default="A threat agent misconfigured inbound connection settings, allowing unauthorized access to sensitive resources", help="Analyst note about service")
    parser.add_argument("--output", help="Output JSON file path")
    
    args = parser.parse_args()
    
    # Run base mapping
    base_mapper = ControlMapper(args.controls)
    base_results = base_mapper.map_controls(args.service, args.doc, args.note)
    
    # Enhance with LLM
    llm_mapper = LLMEnhancedMapper(base_mapper)
    enhanced_results = llm_mapper.enhance_control_mapping(
        args.service, 
        args.doc, 
        args.note, 
        base_results
    )
    
    # Combine results
    combined_results = {
        "base_mapping": base_results,
        "enhanced_mapping": enhanced_results
    }
    
    # Print results
    print(json.dumps(combined_results, indent=2))
    
    # Save results to file if output path provided
    if args.output:
        with open(args.output, "w") as f:
            json.dump(combined_results, f, indent=2)

if __name__ == "__main__":
    main() 