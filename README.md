# Meta-Analysis Data Extraction with Anthropic Citations API

Complete workflow for extracting structured data from research papers and performing meta-analysis with **full citation provenance tracking**.

## 🎯 Overview

This toolkit enables you to:

1. **Extract structured data** from PDF research papers using AI
2. **Track every data point** with precise citations (page numbers, quoted text)
3. **Calculate effect sizes** (OR, RR, SMD) automatically
4. **Perform meta-analysis** (fixed-effect and random-effects models)
5. **Generate publication-ready reports** with audit trails

**Key Feature:** Every extracted number is linked to its exact location in the source paper, providing complete audit trails for systematic reviews.

## 📋 Features

### ✅ Data Extraction
- PDF parsing with sentence-level chunking
- Custom extraction schemas for different study types
- Streaming extraction with real-time feedback
- Batch processing of multiple papers
- Automatic citation tracking

### ✅ Statistical Analysis
- Odds ratios (OR) for dichotomous outcomes
- Risk ratios (RR) for incidence data
- Standardized mean differences (SMD) for continuous outcomes
- Fixed-effect meta-analysis (inverse variance)
- Random-effects meta-analysis (DerSimonian-Laird)
- Heterogeneity assessment (Q, I², τ²)

### ✅ Citation Provenance
- Page-level citations for PDFs
- Character-level citations for plain text
- Block-level citations for custom content
- Citation maps linking data to sources
- HTML reports with clickable citations

## 🚀 Quick Start

### Installation

```bash
# Install required packages
pip install anthropic pandas numpy

# Set your API key
export ANTHROPIC_API_KEY='your-api-key-here'
```

### Basic Usage

```python
from complete_workflow import CompleteMetaAnalysisWorkflow

# Initialize workflow
workflow = CompleteMetaAnalysisWorkflow()

# Define your papers
papers = [
    "path/to/study1.pdf",
    "path/to/study2.pdf",
    "path/to/study3.pdf"
]

# Run complete workflow
workflow.run_complete_workflow(
    pdf_paths=papers,
    study_type="clinical_trial",
    output_dir="./my_meta_analysis"
)
```

This will:
1. Extract data from each PDF
2. Calculate effect sizes
3. Perform meta-analysis
4. Generate HTML report with citations

## 📊 Supported Study Types

### Clinical Trials
```python
workflow.run_complete_workflow(
    pdf_paths=papers,
    study_type="clinical_trial"
)
```

Extracts:
- Study design (RCT, quasi-RCT)
- Sample sizes by group
- Baseline characteristics
- Primary/secondary outcomes
- Effect estimates and CIs
- Risk of bias assessment

### Surgical Studies
```python
workflow.run_complete_workflow(
    pdf_paths=papers,
    study_type="surgical"
)
```

Extracts:
- Surgical procedures
- Operative details
- Mortality rates
- Functional outcomes (mRS, GOS)
- Complication rates
- Hospital stay data

### Observational Studies
```python
workflow.run_complete_workflow(
    pdf_paths=papers,
    study_type="observational"
)
```

Extracts:
- Cohort/case-control data
- Exposure definitions
- Outcome measures
- Adjusted/unadjusted estimates
- Confounders

## 📁 Project Structure

```
.
├── meta_analysis_extractor.py      # Core extraction with Citations API
├── streaming_extractor.py          # Streaming version with progress
├── meta_analysis_calculator.py     # Effect size & meta-analysis
├── complete_workflow.py            # End-to-end workflow
└── README.md                       # This file
```

## 💡 Examples

### Example 1: Single Paper Extraction

```python
from meta_analysis_extractor import MetaAnalysisExtractor

extractor = MetaAnalysisExtractor()

# Define custom schema
schema = {
    "participants": {
        "sample_size": "integer",
        "mean_age": "float"
    },
    "outcomes": {
        "mortality": "integer",
        "complications": "integer"
    }
}

# Extract with citations
result = extractor.extract_from_single_paper(
    "study.pdf",
    extraction_schema=schema
)

print(f"Citations found: {result['citation_count']}")
print(f"Extracted data: {result['extracted_data']}")

# Citations are in result['citations']
for citation in result['citations']:
    print(f"Page {citation['start_page_number']}: {citation['cited_text']}")
```

### Example 2: Streaming Extraction

```python
from streaming_extractor import StreamingMetaAnalysisExtractor

extractor = StreamingMetaAnalysisExtractor()

# Define callbacks for real-time feedback
def on_text(text):
    print(text, end='', flush=True)

def on_citation(citation):
    page = citation.get('start_page_number', '?')
    print(f"\n[Citation found on page {page}]")

# Extract with streaming
result = extractor.extract_with_streaming(
    "study.pdf",
    schema,
    on_text_callback=on_text,
    on_citation_callback=on_citation
)
```

### Example 3: Meta-Analysis

```python
from meta_analysis_calculator import MetaAnalysisCalculator

# Load extraction results
import json
with open("extraction_results.json") as f:
    results = json.load(f)

# Calculate meta-analysis
calculator = MetaAnalysisCalculator(results)
calculator.extract_dichotomous_outcomes()

# Get pooled estimates
fixed_results = calculator.perform_fixed_effect_meta_analysis()
random_results = calculator.perform_random_effects_meta_analysis()

print(f"Pooled OR: {random_results['pooled_effect']:.3f}")
print(f"95% CI: [{random_results['lower_ci']:.3f}, {random_results['upper_ci']:.3f}]")
print(f"I²: {random_results['heterogeneity']['i_squared']:.1f}%")
```

## 🔬 Schema Customization

Create custom schemas for your research domain:

```python
# Example: Cerebellar stroke studies
cerebellar_schema = {
    "imaging": {
        "infarct_volume_ml": "float",
        "hydrocephalus": "boolean",
        "brainstem_compression": "boolean"
    },
    "intervention": {
        "surgical_procedure": "string (SDC, necrosectomy, EVD)",
        "timing_hours": "float"
    },
    "outcomes": {
        "mortality_sdc": "integer",
        "mortality_conservative": "integer",
        "mrs_0_3_sdc": "integer",
        "mrs_0_3_conservative": "integer"
    }
}

workflow.run_complete_workflow(
    papers,
    study_type="surgical",  # Use surgical base
    # Schema will be merged with surgical defaults
)
```

## 📈 Output Files

After running the workflow, you'll get:

```
my_meta_analysis/
├── step1_extraction_complete.json    # Raw extraction with all citations
├── step1_extraction_data.csv         # Tabular data for spreadsheets
├── step1_extraction_citations.json   # Citation map by study
├── step3_meta_analysis_results.json  # Statistical analysis results
└── FINAL_META_ANALYSIS_REPORT.html   # Interactive HTML report
```

### HTML Report Includes:
- **Overview**: Study counts, citation counts, heterogeneity
- **Results**: Fixed-effect and random-effects pooled estimates
- **Forest plot data**: Individual study results with CIs
- **Heterogeneity assessment**: Q, I², τ² statistics
- **Citation tracking**: Every data point linked to source

## 🎨 Advanced Features

### Custom Citation Handling

```python
# Access individual citations
for result in extraction_results:
    for citation in result['citations']:
        if citation['type'] == 'page_location':
            print(f"PDF: Pages {citation['start_page_number']}-{citation['end_page_number']}")
            print(f"Text: {citation['cited_text']}")
```

### Batch Processing with Progress

```python
def progress_callback(current, total, message):
    print(f"[{current}/{total}] {message}")

results = extractor.extract_batch_with_progress(
    pdf_files,
    schema,
    progress_callback=progress_callback
)
```

### Export to Multiple Formats

```python
# Export to DataFrame
df = extractor.export_to_dataframe(results)
df.to_excel("extracted_data.xlsx", index=False)

# Export citation report
extractor.generate_citation_report(
    results,
    output_path="citations.html"
)
```

## 📊 Statistical Methods

### Effect Size Calculations

#### Odds Ratio (OR)
```python
log_or, se, lower_ci, upper_ci = calculator.calculate_odds_ratio(
    events_treatment=10,
    n_treatment=50,
    events_control=20,
    n_control=50
)
```

#### Risk Ratio (RR)
```python
log_rr, se, lower_ci, upper_ci = calculator.calculate_risk_ratio(
    events_treatment=10,
    n_treatment=50,
    events_control=20,
    n_control=50
)
```

#### Standardized Mean Difference (Hedges' g)
```python
hedges_g, se, lower_ci, upper_ci = calculator.calculate_standardized_mean_difference(
    mean_treatment=5.2,
    sd_treatment=1.3,
    n_treatment=50,
    mean_control=3.8,
    sd_control=1.1,
    n_control=50
)
```

### Meta-Analysis Models

#### Fixed-Effect (Inverse Variance)
- Assumes one true effect size
- Weights studies by precision (1/variance)
- Appropriate when I² < 25%

#### Random-Effects (DerSimonian-Laird)
- Accounts for between-study heterogeneity
- Adds τ² (tau-squared) to variance
- Recommended when I² > 25%

## 🔍 Citation Quality

Citations are tracked at multiple levels:

1. **Page-level**: For PDF documents
2. **Sentence-level**: Automatic chunking
3. **Custom-level**: User-defined granularity

Every extracted value includes:
- Source text (exact quote)
- Location (page/character position)
- Document reference
- Full citation object for traceability

## ⚙️ Configuration

### API Settings

```python
# Custom model or settings
extractor = MetaAnalysisExtractor(api_key="your-key")
extractor.model = "claude-sonnet-4-5"
```

### Extraction Parameters

```python
# Customize max tokens for longer papers
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=8192,  # Increase for complex papers
    messages=[...]
)
```

## 🐛 Troubleshooting

### PDF Text Extraction Issues
- Ensure PDFs contain extractable text (not scanned images)
- Use OCR preprocessing if needed
- Check page numbers match paper

### Missing Citations
- Verify citations are enabled: `"citations": {"enabled": True}`
- Check that data exists in source document
- Review extraction prompt specificity

### JSON Parsing Errors
- Ensure response format is strictly JSON
- Add explicit JSON-only instructions to prompt
- Use error handling with fallback parsing

## 📝 Best Practices

1. **Schema Design**: Be specific about data types and units
2. **Prompt Engineering**: Explicitly request citations for numerical data
3. **Quality Control**: Manually verify a sample of extractions
4. **Batch Size**: Process 5-10 papers at a time for manageable review
5. **Version Control**: Save extraction results for reproducibility

## 🤝 Use Cases

### Systematic Reviews
- Extract data for PRISMA-compliant reviews
- Track citation provenance for transparency
- Generate audit trails for journal submission

### Network Meta-Analysis
- Extract comparative effectiveness data
- Maintain treatment arm citations
- Export to specialized NMA software

### Individual Patient Data (IPD) Meta-Analysis
- Extract patient-level characteristics when available
- Track outcome definitions across studies
- Map heterogeneous outcomes

## 📚 References

- Anthropic Citations API Documentation
- Cochrane Handbook for Systematic Reviews
- PRISMA Statement Guidelines
- DerSimonian & Laird (1986) - Random-effects meta-analysis

## 🔗 Resources

- [Anthropic API Docs](https://docs.anthropic.com)
- [Citations Feature](https://docs.anthropic.com/en/docs/build-with-claude/citations)
- [PDF Support](https://docs.anthropic.com/en/docs/build-with-claude/pdf-support)

## 📄 License

MIT License - Feel free to use and modify for your research

## 🙏 Acknowledgments

Built with Anthropic's Claude and Citations API to advance evidence-based medicine through better systematic review tools.

---

**Questions?** Check the examples or create an issue with your use case.

**Contributing:** Pull requests welcome! Please test with sample papers first.
