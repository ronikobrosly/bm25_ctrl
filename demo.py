#!/usr/bin/env python3
"""
Demo script for the Control Mapping Pipeline.
This script demonstrates how to use the pipeline for mapping cloud services to control policies.
"""

import os
import json
import argparse
from ctrl_mapping import ControlMapper

def setup_demo_directories():
    """Create necessary directories for the demo."""
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)

def run_demo(controls_file, doc_file, service_name, analyst_note):
    """Run a demo of the control mapping pipeline.
    
    Args:
        controls_file: Path to controls CSV file
        doc_file: Path to service documentation PDF
        service_name: Name of cloud service
        analyst_note: Analyst's note about service
    """
    # Initialize control mapper
    print(f"\n1. Initializing Control Mapper with {controls_file}...")
    mapper = ControlMapper(controls_file)
    print(f"   Loaded {len(mapper.controls)} control policies")
    
    # Map controls for service
    print(f"\n2. Mapping controls for {service_name}...")
    print(f"   Using documentation: {doc_file}")
    print(f"   Analyst note: {analyst_note}")
    
    result = mapper.map_controls(service_name, doc_file, analyst_note)
    
    # Save results
    output_file = f"output/{service_name.replace(' ', '_').lower()}_controls.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    # Print results
    print(f"\n3. Results saved to {output_file}")
    print("\nTop control policies mapped to this service:")
    print("-" * 80)
    
    # Get the inner dictionary of control IDs to confidence levels
    controls_dict = result.get(service_name, {})
    
    # Print each control with description and confidence
    for control_id, confidence in controls_dict.items():
        control_id = int(control_id)  # Convert string ID to integer
        description = mapper.get_control_description(control_id)
        print(f"Control {control_id}:")
        print(f"   Description: {description}")
        print(f"   Confidence: {confidence}")
        print("-" * 80)
    
    return result

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Demo for Control Mapping Pipeline")
    parser.add_argument("--controls", default="data/controls.csv", help="Path to controls CSV file")
    parser.add_argument("--doc", default="data/timestream_security.pdf", help="Path to service documentation PDF")
    parser.add_argument("--service", default="AWS Timestream", help="Name of cloud service")
    parser.add_argument("--note", default="A threat agent misconfigured inbound connection settings, accept lists, and/or VPC firewall rules, allowing them to bypass security controls and gain unauthorized access to sensitive resources and APIs, leading to the theft or disclosure of highly confidential data", help="Analyst note about service")
    
    args = parser.parse_args()
    
    # Create demo directories
    setup_demo_directories()
    
    # Run demo
    run_demo(args.controls, args.doc, args.service, args.note)

if __name__ == "__main__":
    main() 