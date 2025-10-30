# Usage Guide: Meta-Analysis with Citations API

## Table of Contents
1. [Quick Start](#quick-start)
2. [Basic Workflow](#basic-workflow)
3. [Advanced Usage](#advanced-usage)
4. [Customization](#customization)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY='your-api-key'
```

### Run Minimal Example
```bash
python minimal_example.py
```

---

## Basic Workflow

### Scenario 1: Extract Data from Single Paper

```python
from meta_analysis_extractor import MetaAnalysisExtractor

# Initialize
extractor = MetaAnalysisExtractor()

# Define what to extract
schema = {
    "study_info": {
        "first_author": "string",
        "year": "integer"
    },
    "participants": {
        "sample_size": "integer"
    },
    "outcomes": {
        "mortality_treatment": "integer",
        "mortality_control": "integer"
    }
}

# Extract with citations
result = extractor.extract_from_single_paper(
    pdf_path="my_paper.pdf",
    extraction_schema=schema
)

# View results
print(f"Extracted data: {result['extracted_data']}")
print(f"Citations: {result['citation_count']}")

# Access individual citations
for citation in result['citations']:
    print(f"Page {citation['start_page_number']}: {citation['cited_text']}")
```

**Output Structure:**
```python
{
    "document_title": "my_paper.pdf",
    "extracted_data": {
        "study_info": {
            "first_author": "Smith",
            "year": 2023
        },
        "participants": {
            "sample_size": 150
        },
        "outcomes": {
            "mortality_treatment": 10,
            "mortality_control": 25
        }
    },
    "citations": [
        {
            "type": "page_location",
            "cited_text": "A total of 150 patients were enrolled...",
            "document_index": 0,
            "document_title": "my_paper.pdf",
            "start_page_number": 5,
            "end_page_number": 6
        },
        # ... more citations
    ],
    "citation_count": 8
}
```

---

### Scenario 2: Batch Processing Multiple Papers

```python
# List of papers to process
papers = [
    "study1.pdf",
    "study2.pdf",
    "study3.pdf",
    "study4.pdf",
    "study5.pdf"
]

# Extract from all papers
results = extractor.extract_from_multiple_papers(
    pdf_paths=papers,
    extraction_schema=schema
)

# Save results
extractor.save_results(
    results,
    output_dir="./output",
    prefix="batch_extraction"
)

# Files created:
# - batch_extraction_complete.json (all data + citations)
# - batch_extraction_data.csv (tabular format)
# - batch_extraction_citations.json (citation map)
```

---

### Scenario 3: Perform Meta-Analysis

```python
from meta_analysis_calculator import MetaAnalysisCalculator

# Load extraction results
with open("batch_extraction_complete.json") as f:
    results = json.load(f)

# Calculate effect sizes
calculator = MetaAnalysisCalculator(results)
calculator.extract_dichotomous_outcomes()

# Run meta-analysis
fixed_results = calculator.perform_fixed_effect_meta_analysis()
random_results = calculator.perform_random_effects_meta_analysis()

# Print summary
calculator.print_summary(fixed_results, random_results)

# Export results
calculator.export_results(
    fixed_results,
    random_results,
    output_path="meta_analysis_results.json"
)
```

**Output:**
```
======================================================================
META-ANALYSIS RESULTS
======================================================================

Number of studies included: 5
Total citations tracked: 47

--- FIXED-EFFECT MODEL ---
Pooled Odds Ratio: 0.421
95% CI: [0.289, 0.614]
Z = -4.231, p = 0.0000

--- RANDOM-EFFECTS MODEL ---
Pooled Odds Ratio: 0.398
95% CI: [0.231, 0.687]
Z = -3.156, p = 0.0016

--- HETEROGENEITY ---
Q = 8.45 (df = 4), p = 0.0763
I² = 52.7%
τ² = 0.1234

--- INTERPRETATION ---
Moderate heterogeneity detected
Statistically significant pooled effect (p < 0.05)
```

---

### Scenario 4: Complete End-to-End Workflow

```python
from complete_workflow import CompleteMetaAnalysisWorkflow

# Initialize
workflow = CompleteMetaAnalysisWorkflow()

# Define papers
papers = ["study1.pdf", "study2.pdf", "study3.pdf"]

# Run complete workflow
workflow.run_complete_workflow(
    pdf_paths=papers,
    study_type="clinical_trial",
    output_dir="./my_meta_analysis"
)

# Output files:
# ./my_meta_analysis/
# ├── step1_extraction_complete.json
# ├── step1_extraction_data.csv
# ├── step1_extraction_citations.json
# ├── step3_meta_analysis_results.json
# └── FINAL_META_ANALYSIS_REPORT.html  ← Open this!
```

---

## Advanced Usage

### Custom Extraction Schema

#### For Cerebellar Stroke Studies
```python
cerebellar_schema = {
    "patient_characteristics": {
        "total_patients": "integer",
        "mean_age": "float",
        "percent_male": "float"
    },
    "imaging": {
        "mean_infarct_volume_ml": "float",
        "hydrocephalus_n": "integer",
        "brainstem_compression_n": "integer"
    },
    "intervention": {
        "sdc_performed": "integer",
        "conservative_management": "integer",
        "mean_time_to_surgery_hours": "float"
    },
    "outcomes": {
        "mortality_sdc": "integer",
        "mortality_conservative": "integer",
        "mrs_0_3_sdc": "integer (favorable outcome)",
        "mrs_0_3_conservative": "integer (favorable outcome)",
        "mrs_at_discharge": "string (median or mean)"
    },
    "timing": {
        "symptom_onset_to_surgery_hours": "float",
        "admission_to_surgery_hours": "float"
    }
}

result = extractor.extract_from_single_paper(
    "cerebellar_study.pdf",
    extraction_schema=cerebellar_schema
)
```

#### For Drug Trials
```python
drug_trial_schema = {
    "trial_design": {
        "phase": "string (I, II, III, IV)",
        "randomization": "string (simple, stratified, block)",
        "blinding": "string (single, double, triple)",
        "placebo_controlled": "boolean"
    },
    "intervention": {
        "drug_name": "string",
        "dose": "string",
        "frequency": "string",
        "duration": "string",
        "route": "string (oral, IV, etc.)"
    },
    "efficacy_outcomes": {
        "primary_endpoint": "string",
        "response_rate_treatment": "float (percentage)",
        "response_rate_placebo": "float (percentage)",
        "mean_change_treatment": "float",
        "mean_change_placebo": "float"
    },
    "safety_outcomes": {
        "adverse_events_treatment": "integer",
        "adverse_events_placebo": "integer",
        "serious_adverse_events_treatment": "integer",
        "serious_adverse_events_placebo": "integer",
        "discontinuations_treatment": "integer",
        "discontinuations_placebo": "integer"
    }
}
```

---

### Streaming with Real-Time Feedback

```python
from streaming_extractor import StreamingMetaAnalysisExtractor

extractor = StreamingMetaAnalysisExtractor()

# Define callbacks
def on_text(text):
    print(text, end='', flush=True)

def on_citation(citation):
    page = citation.get('start_page_number', '?')
    print(f"\n📌 Citation found on page {page}")

# Extract with streaming
result = extractor.extract_with_streaming(
    "paper.pdf",
    schema,
    on_text_callback=on_text,
    on_citation_callback=on_citation
)
```

---

### Batch Processing with Progress Tracking

```python
def progress_callback(current, total, message):
    percent = (current / total) * 100
    print(f"\r[{current}/{total}] {percent:.0f}% - {message}", end='')

results = extractor.extract_batch_with_progress(
    pdf_files,
    schema,
    progress_callback=progress_callback
)

# Output:
# [1/5] 20% - Processing study1.pdf
# [1/5] 20% - Extracting... {"study_info"...
# [1/5] 20% - Citation found (page 3): mortality data
# [2/5] 40% - Processing study2.pdf
# ...
```

---

### Working with Different Effect Sizes

#### Risk Ratio (for cohort studies)
```python
log_rr, se, lower_ci, upper_ci = calculator.calculate_risk_ratio(
    events_treatment=15,
    n_treatment=100,
    events_control=30,
    n_control=100
)

print(f"Risk Ratio: {np.exp(log_rr):.3f}")
print(f"95% CI: [{lower_ci:.3f}, {upper_ci:.3f}]")
```

#### Standardized Mean Difference (for continuous outcomes)
```python
hedges_g, se, lower_ci, upper_ci = calculator.calculate_standardized_mean_difference(
    mean_treatment=75.5,
    sd_treatment=12.3,
    n_treatment=50,
    mean_control=68.2,
    sd_control=11.8,
    n_control=50
)

print(f"Hedges' g: {hedges_g:.3f}")
print(f"95% CI: [{lower_ci:.3f}, {upper_ci:.3f}]")
```

---

### Export to Different Formats

```python
# Export to DataFrame
df = extractor.export_to_dataframe(results, include_citations=True)

# Save to Excel
df.to_excel("extracted_data.xlsx", index=False)

# Save to CSV
df.to_csv("extracted_data.csv", index=False)

# Generate HTML citation report
extractor.generate_citation_report(
    results,
    output_path="citation_report.html"
)
```

---

## Customization

### Custom Prompts

```python
def create_custom_prompt(schema):
    return f"""You are an expert in systematic review data extraction.

Extract the following data from this research paper with MAXIMUM PRECISION:

{json.dumps(schema, indent=2)}

CRITICAL RULES:
1. Use citations for EVERY numerical value
2. If data is in a table, cite the table number AND page
3. If data is in text, quote the exact sentence
4. For mortality: clearly distinguish between in-hospital vs 30-day vs 90-day
5. For functional outcomes: note the scale used (mRS, GOS, Barthel, etc.)
6. Return ONLY valid JSON - no additional text

Extract now:"""

# Use custom prompt
prompt = create_custom_prompt(schema)
# ... then use in API call
```

---

### Custom Citation Handling

```python
def analyze_citation_quality(result):
    """Check quality of citations"""
    citations = result['citations']
    
    # Check citation density
    citation_density = len(citations) / len(result['extracted_data'].keys())
    
    # Check for specific fields
    numerical_fields = ['sample_size', 'mortality', 'mean_age']
    cited_numerical = sum(
        1 for c in citations 
        if any(field in c['cited_text'].lower() for field in numerical_fields)
    )
    
    print(f"Citation density: {citation_density:.2f} citations per field")
    print(f"Numerical fields cited: {cited_numerical}/{len(numerical_fields)}")
    
    # Warn if low citation coverage
    if citation_density < 0.5:
        print("⚠️  Warning: Low citation coverage. Consider reprompting.")
    
    return {
        "density": citation_density,
        "numerical_coverage": cited_numerical / len(numerical_fields)
    }

# Use it
quality = analyze_citation_quality(result)
```

---

## Troubleshooting

### Issue: Citations Not Appearing

**Cause:** Citations not enabled
```python
# ❌ Wrong
{
    "type": "document",
    "source": {...}
    # Missing citations parameter
}

# ✅ Correct
{
    "type": "document",
    "source": {...},
    "citations": {"enabled": True}  # ← Must include this!
}
```

---

### Issue: JSON Parsing Errors

**Solution:** Add strict formatting instructions
```python
prompt = """
Extract data and return as JSON.

CRITICAL: Your ENTIRE response must be ONLY valid JSON.
Do NOT include:
- Explanatory text before or after the JSON
- Markdown code blocks (```json)
- Comments inside the JSON

Just return the raw JSON object.
"""
```

---

### Issue: Missing Data in Extraction

**Solution 1:** Improve prompt specificity
```python
# Instead of:
"mortality": "integer"

# Use:
"mortality_intervention": "integer - number of deaths in intervention group (table 2 or results section)"
"mortality_control": "integer - number of deaths in control group (table 2 or results section)"
```

**Solution 2:** Multi-pass extraction
```python
# First pass: broad extraction
result1 = extractor.extract_from_single_paper(pdf, general_schema)

# Second pass: targeted extraction for missing fields
missing_fields = {k: v for k, v in schema.items() if result1[k] is None}
result2 = extractor.extract_from_single_paper(pdf, missing_fields)

# Merge results
final_result = {**result1, **result2}
```

---

### Issue: Heterogeneous Reporting Across Studies

**Solution:** Use flexible schema with multiple field options
```python
outcomes_schema = {
    # Try multiple possible field names
    "mortality": "integer - deaths at any timepoint",
    "mortality_30day": "integer - deaths within 30 days",
    "mortality_90day": "integer - deaths within 90 days",
    "mortality_hospital": "integer - in-hospital deaths",
    
    # Add context field
    "mortality_timepoint": "string - when mortality was assessed",
    "mortality_source": "string - where in paper this came from (e.g., Table 3)"
}

# Then in analysis, handle variants:
def get_mortality(data):
    """Get mortality, handling different timepoints"""
    for field in ['mortality_30day', 'mortality_90day', 'mortality_hospital', 'mortality']:
        if data.get(field) is not None:
            return data[field], field
    return None, None
```

---

### Issue: Large PDF Processing Time

**Solution 1:** Use streaming for real-time feedback
```python
extractor = StreamingMetaAnalysisExtractor()
result = extractor.extract_with_streaming(large_pdf, schema)
```

**Solution 2:** Split extraction by sections
```python
# Extract demographics separately from outcomes
demographics_result = extractor.extract_from_single_paper(pdf, demographics_schema)
outcomes_result = extractor.extract_from_single_paper(pdf, outcomes_schema)

# Merge
complete_result = {**demographics_result, **outcomes_result}
```

---

## Tips & Best Practices

### 1. Start with a Pilot Study
```python
# Test on 2-3 papers first
pilot_papers = papers[:3]
pilot_results = extractor.extract_from_multiple_papers(pilot_papers, schema)

# Review quality
for result in pilot_results:
    print(f"Study: {result['document_title']}")
    print(f"Citations: {result['citation_count']}")
    print(f"Extracted fields: {len(result['extracted_data'])}")
    
# Adjust schema if needed before processing all papers
```

### 2. Version Your Extraction Schema
```python
SCHEMA_VERSION = "2.1"

schema = {
    "_version": SCHEMA_VERSION,
    "_description": "Updated to include surgical timing",
    # ... rest of schema
}

# Save with version
with open(f"schema_v{SCHEMA_VERSION}.json", 'w') as f:
    json.dump(schema, f, indent=2)
```

### 3. Keep Extraction Logs
```python
import logging

logging.basicConfig(
    filename='extraction_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

for paper in papers:
    logging.info(f"Starting extraction: {paper}")
    try:
        result = extractor.extract_from_single_paper(paper, schema)
        logging.info(f"Success: {result['citation_count']} citations")
    except Exception as e:
        logging.error(f"Failed: {str(e)}")
```

### 4. Validate Extracted Data
```python
def validate_study_data(data):
    """Basic validation checks"""
    issues = []
    
    # Check required fields
    required = ['first_author', 'year', 'sample_size']
    for field in required:
        if not data.get(field):
            issues.append(f"Missing required field: {field}")
    
    # Check logical consistency
    if data.get('mortality_intervention', 0) > data.get('intervention_group_size', float('inf')):
        issues.append("Mortality exceeds group size in intervention")
    
    # Check year range
    year = data.get('year')
    if year and (year < 1950 or year > 2025):
        issues.append(f"Suspicious year: {year}")
    
    return issues

# Use it
for result in results:
    issues = validate_study_data(result['extracted_data'])
    if issues:
        print(f"⚠️  Issues in {result['document_title']}:")
        for issue in issues:
            print(f"  - {issue}")
```

---

## Real-World Example: Cerebellar Stroke Meta-Analysis

```python
# Complete workflow for cerebellar stroke SDC meta-analysis
from complete_workflow import CompleteMetaAnalysisWorkflow

workflow = CompleteMetaAnalysisWorkflow()

# Papers identified from systematic search
papers = [
    "jauss_1999.pdf",
    "raco_2003.pdf",
    "pfefferkorn_2009.pdf",
    "koh_2012.pdf",
    "walker_2022.pdf"
]

# Define cerebellar-specific schema
cerebellar_schema = workflow.define_extraction_schema("surgical")

# Run workflow
workflow.run_complete_workflow(
    pdf_paths=papers,
    study_type="surgical",
    output_dir="./cerebellar_sdc_meta"
)

# Results will include:
# - Individual study ORs for mortality (SDC vs conservative)
# - Pooled OR with 95% CI
# - Heterogeneity statistics
# - Complete citation trail for each data point
# - HTML report ready for appendix in systematic review paper
```

---

## Questions?

For more examples, see:
- `minimal_example.py` - Simplest possible usage
- `complete_workflow.py` - Full end-to-end workflow
- `streaming_extractor.py` - Real-time progress tracking

For issues or questions, review the main README.md or check the Anthropic documentation.
