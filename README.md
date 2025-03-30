# Cloud Service Control Mapping Pipeline

A pipeline for mapping cloud services to security control policies using BM25 retrieval.


## Overview

This is a complete pipeline for mapping cloud services to security control policies using BM25 retrieval. System Architecture


### System Architecture

The pipeline consists of several components working together:

1) Core Control Mapper (ctrl_mapping.py)
* This is the heart of the system, implementing BM25 retrieval to identify relevant controls
* Handles loading controls from CSV, processing PDF documentation, and generating mappings

2) LLM Enhancement Layer (llm_enhanced_mapping.py)
* Extends the base retrieval with LLama 3.1 70B capabilities
* Provides more nuanced assessment of control applicability with justifications

3) Utility Scripts
* create_test_pdf.py: Converts text to PDF for testing
* run_pipeline.sh / run_pipeline.ps1: Orchestration scripts to run the entire pipeline

### Here's how the inputs are processed through the pipeline:

1) Control Policies CSV → Loaded and preprocessed for BM25 indexing
* Each control description is tokenized and indexed
* Control IDs are preserved for the final mapping

2) Cloud Service Documentation PDF → Processed to extract security-relevant sections
* The pipeline uses regex patterns to identify security-related content
* This focuses the analysis on the most relevant parts of the documentation

3) Analyst's Threat Description → Combined with service name and security text
* Creates a comprehensive query that captures security context
* Used to score controls based on relevance

4) BM25 Scoring → Ranks controls by relevance to the service context
* Normalizes scores to assign confidence levels (high/medium/low)
* Creates the initial mapping recommendation

5) LLM Enhancement (optional) → Refines mappings with deeper analysis
* Reviews top controls identified by BM25
* Provides justifications for recommendations


## How to use the pipeline

### For Each New Cloud Service

1) Prepare your inputs:
* Place your control policies CSV in the data directory
* Save the cloud service documentation PDF in the data directory
* Prepare your analyst threat paragraph

2) Run the pipeline
```
# On Linux/Mac
   ./run_pipeline.sh --controls data/your_controls.csv --service "AWS New Service" --doc data/service_doc.pdf --note "Your analyst threat paragraph"
   
# On Windows
   .\run_pipeline.ps1 --controls data\your_controls.csv --service "AWS New Service" --doc data\service_doc.pdf --note "Your analyst threat paragraph"
```

3) Review the results

* Output JSON file will be created in the output directory
* The format matches your required structure
* Output should look like this:
{
     "AWS New Service": {
       "3": "low",
       "44": "high",
       "423": "medium",
       "333": "high"
     }
}

Where integers represent controls 