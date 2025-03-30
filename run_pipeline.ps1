# Run the entire control mapping pipeline

# Create necessary directories
if (-not (Test-Path -Path "data")) {
    New-Item -Path "data" -ItemType Directory
}
if (-not (Test-Path -Path "output")) {
    New-Item -Path "output" -ItemType Directory
}

# Check for virtual environment
if (-not (Test-Path -Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
} else {
    .\venv\Scripts\Activate.ps1
}

# Default values
$controlsFile = "data\controls.csv"
$serviceName = "AWS Timestream"
$docFile = "data\timestream_security.pdf"
$analystNote = "A threat agent misconfigured inbound connection settings, accept lists, and/or VPC firewall rules, allowing them to bypass security controls and gain unauthorized access to sensitive resources and APIs, leading to the theft or disclosure of highly confidential data"
$outputDir = "output"

# Parse command line arguments
for ($i = 0; $i -lt $args.Count; $i++) {
    switch ($args[$i]) {
        "--controls" {
            $controlsFile = $args[$i+1]
            $i++
        }
        "--service" {
            $serviceName = $args[$i+1]
            $i++
        }
        "--doc" {
            $docFile = $args[$i+1]
            $i++
        }
        "--note" {
            $analystNote = $args[$i+1]
            $i++
        }
        "--output" {
            $outputDir = $args[$i+1]
            $i++
        }
        default {
            Write-Host "Unknown option: $($args[$i])"
            exit 1
        }
    }
}

# Check if the doc file is a text file rather than PDF
if ($docFile -like "*.txt") {
    Write-Host "Converting text file to PDF..."
    $pdfFile = $docFile -replace "\.txt$", ".pdf"
    python create_test_pdf.py --input $docFile --output $pdfFile
    $docFile = $pdfFile
}

# Run the control mapping
Write-Host "Running control mapping pipeline..."
python demo.py --controls $controlsFile --service $serviceName --doc $docFile --note $analystNote

# Run LLM-enhanced mapping if available
if (Test-Path -Path "llm_enhanced_mapping.py") {
    Write-Host "Running LLM-enhanced mapping..."
    $outputFile = Join-Path -Path $outputDir -ChildPath ($serviceName -replace " ", "_") + "_enhanced.json"
    python llm_enhanced_mapping.py --controls $controlsFile --service $serviceName --doc $docFile --note $analystNote --output $outputFile
}

Write-Host "Pipeline completed successfully!"
Write-Host "Results available in: $outputDir" 