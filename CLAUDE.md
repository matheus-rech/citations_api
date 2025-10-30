# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based meta-analysis toolkit that extracts structured data from research papers (PDFs) using Anthropic's Claude API with Citations feature. Every extracted data point is tracked with precise source citations (page numbers, quoted text), enabling complete audit trails for systematic reviews.

**Core capabilities:**
- Schema-driven data extraction from PDFs
- Statistical effect size calculations (OR, RR, SMD)
- Fixed-effect and random-effects meta-analysis
- HTML report generation with citation provenance

## Commands

### Installation
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY='your-api-key-here'
```

### Running Examples
```bash
# Minimal example - single paper extraction with citations
python minimal_example.py

# Complete workflow - multi-paper extraction + meta-analysis + report generation
python complete_workflow.py

# Streaming extraction - real-time progress feedback
python streaming_extractor.py
```

### Testing
No formal test suite exists. Integration testing is done via the example scripts above.

**Action Item:** A formal test suite using a framework like `pytest` should be established to ensure correctness and prevent regressions. This is a high-priority task for project health.

## Architecture Overview

### 4-Step Pipeline

The `CompleteMetaAnalysisWorkflow` orchestrates an end-to-end pipeline:

```
STEP 1: Data Extraction
  ├─ Load PDFs and convert to base64
  ├─ Generate extraction prompts from schemas
  ├─ Call Claude API with citations enabled
  └─ Parse responses and extract citations
         ↓
STEP 2: Effect Size Calculation
  ├─ Calculate OR/RR/SMD with confidence intervals
  └─ Apply continuity corrections for zero cells
         ↓
STEP 3: Meta-Analysis
  ├─ Fixed-effect (inverse variance weighting)
  ├─ Random-effects (DerSimonian-Laird)
  └─ Heterogeneity assessment (Q, I², τ²)
         ↓
STEP 4: Report Generation
  └─ Generate HTML with clickable citations
```

### Three Extraction Patterns

1. **Standard extraction** (`MetaAnalysisExtractor`): Full response collection, batch processing
2. **Streaming extraction** (`StreamingMetaAnalysisExtractor`): Real-time callbacks for text chunks and citations
3. **Batch processing** (`extract_from_multiple_papers`): Multi-document workflows

## Core Modules

### meta_analysis_extractor.py (512 lines)
Core extraction engine using Anthropic Citations API.

**Key class:** `MetaAnalysisExtractor`

**Main methods:**
- `extract_from_single_paper(pdf_path, extraction_schema)` - Single PDF extraction
- `extract_from_multiple_papers(pdf_paths, extraction_schema)` - Batch processing
- `export_to_dataframe(results)` - Convert to pandas DataFrame
- `save_results(results, output_prefix)` - Export to JSON/CSV

**Important:** Always enables citations via `extra_body={"citations": {"enabled": True}}` when calling the API.

### meta_analysis_calculator.py (520+ lines)
Statistical calculations and meta-analysis.

**Key class:** `MetaAnalysisCalculator`

**Effect size methods:**
- `calculate_odds_ratio(events_treatment, n_treatment, events_control, n_control)` - Returns (log_or, se, lower_ci, upper_ci)
- `calculate_risk_ratio(...)` - For cohort/prospective studies
- `calculate_standardized_mean_difference(mean_t, sd_t, n_t, mean_c, sd_c, n_c)` - Hedges' g with bias correction

**Meta-analysis methods:**
- `perform_fixed_effect_meta_analysis()` - Inverse variance weighting
- `perform_random_effects_meta_analysis()` - DerSimonian-Laird τ² estimator
- `extract_dichotomous_outcomes()` - Prepare data from extraction results
- `extract_continuous_outcomes()` - Extract means/SDs for SMD

**Statistical outputs:**
- Pooled effect estimates with 95% CI
- Q-statistic and p-value for heterogeneity
- I² (percentage of heterogeneity)
- τ² (between-study variance)

### streaming_extractor.py (350+ lines)
Real-time extraction with progress monitoring.

**Key class:** `StreamingMetaAnalysisExtractor`

**Main method:**
- `extract_with_streaming(pdf_path, schema, on_text_callback, on_citation_callback)` - Provides callbacks for incremental updates

**Use case:** Long documents or when progress feedback is needed.

### complete_workflow.py (500+ lines)
End-to-end orchestration class.

**Key class:** `CompleteMetaAnalysisWorkflow`

**Main method:**
- `run_complete_workflow(pdf_paths, study_type, output_dir)` - Executes all 4 steps

**Supported study types:**
- `"clinical_trial"` - RCTs, sample sizes, outcomes, risk of bias
- `"surgical"` - Procedures, mortality, functional outcomes (mRS, GOS), complications
- `"observational"` - Cohort/case-control, exposures, adjusted estimates

**Schema customization:** Schemas are defined in `get_extraction_schema(study_type)`. Extend or modify these for custom research domains.

## Schema-Driven Extraction

Schemas define what data to extract. Structure:

```python
schema = {
    "category_name": {
        "field_name": "data_type_description",
        "another_field": "data_type_description"
    }
}
```

Example:
```python
schema = {
    "participants": {
        "sample_size": "integer",
        "mean_age": "float",
        "percent_male": "float"
    },
    "outcomes": {
        "mortality_treatment": "integer",
        "mortality_control": "integer"
    }
}
```

**Important:** Be explicit about data types and units in field descriptions. The AI uses these to understand extraction requirements.

## Data Classes and Citations

### Core Data Structures

All in `meta_analysis_extractor.py`:

```python
@dataclass
class Citation:
    type: str  # "page_location", "char_location", "block_location"
    cited_text: str
    start_page_number: Optional[int]
    end_page_number: Optional[int]
    # ... other fields

@dataclass
class ExtractedDataPoint:
    field_name: str
    value: Any
    citations: List[Citation]

@dataclass
class StudyData:
    study_id: str
    extracted_data: Dict[str, Any]
    citations: List[Citation]
```

### Citations as First-Class Objects

**Critical pattern:** Every extracted numerical value maintains a link to its source citation. This enables:
- Verification of extracted data
- Audit trails for systematic reviews
- HTML reports with clickable source references

When working with extraction results, citations are available in:
- `result['citations']` - List of all citations
- `result['citation_count']` - Total count
- `result['extracted_data']` - Data with embedded citation references

## Output Structure

After running `CompleteMetaAnalysisWorkflow.run_complete_workflow()`, the output directory contains:

```
output_dir/
├── step1_extraction_complete.json    # Raw extraction with full citations
├── step1_extraction_data.csv         # Tabular data (importable to Excel)
├── step1_extraction_citations.json   # Citation map by study
├── step3_meta_analysis_results.json  # Statistical results (OR, CI, I², τ²)
└── FINAL_META_ANALYSIS_REPORT.html   # Interactive report
```

**JSON structure of extraction results:**
```json
{
  "study_id": "study_name",
  "extracted_data": {...},
  "citations": [
    {
      "type": "page_location",
      "cited_text": "quoted text from paper",
      "start_page_number": 5,
      "end_page_number": 5
    }
  ],
  "citation_count": 12
}
```

## Important Patterns

### 1. PDF to Base64 Conversion
All PDFs must be base64-encoded before sending to the API. This is handled automatically by `MetaAnalysisExtractor._encode_pdf_to_base64()`.

### 2. Prompt Engineering for Citations
Extraction prompts explicitly request citations:
```python
prompt = f"""Extract the following data from the research paper.
For each numerical value, ensure you cite the exact source.

Schema: {json.dumps(schema, indent=2)}

Return response as JSON matching the schema structure."""
```

### 3. API Call Pattern
```python
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {"type": "base64", "media_type": "application/pdf", "data": base64_pdf},
                    "citations": {"enabled": True}  # Critical for citation tracking
                },
                {"type": "text", "text": prompt}
            ]
        }
    ]
)

### 4. Zero-Cell Continuity Correction
In `calculate_odds_ratio()` and `calculate_risk_ratio()`, a 0.5 continuity correction is applied when any cell has zero events. This prevents division by zero and infinite confidence intervals.

### 5. Effect Size Citations
The `MetaAnalysisCalculator` preserves citations through all calculations. Effect sizes maintain links to their source data points and original paper citations.

## File Locations

- Core modules: All `.py` files should be moved to a `src/` directory for better project structure and packaging.
- Documentation: `README.md`, `QUICK_START.md`, `USAGE_GUIDE.md`
- Sample report template: `index.html`
- Dependencies: `requirements.txt`

## API Requirements

**Environment variable required:** `ANTHROPIC_API_KEY`

**Model used:** `claude-sonnet-4-5` (hardcoded in extractors). This should be refactored into a configurable constant.

**API features used:**
- PDF document support (base64 encoded)
- Citations API (`extra_body={"citations": {"enabled": True}}`)
- Streaming API for `StreamingMetaAnalysisExtractor`

## Common Modifications

### Adding a New Study Type
1. Add schema definition in `CompleteMetaAnalysisWorkflow.get_extraction_schema()`
2. Define category structure and field types
3. Update `run_complete_workflow()` to handle the new type

### Customizing Statistical Methods
Modify `MetaAnalysisCalculator` methods. Current implementations:
- OR/RR: Log-transformed with normal approximation
- SMD: Hedges' g (bias-corrected Cohen's d)
- Meta-analysis: Inverse variance weighting (fixed), DerSimonian-Laird (random)

### Changing Output Format
HTML template is inline in `CompleteMetaAnalysisWorkflow.generate_html_report()`. Modify this method to customize report appearance.

## Best Practices from Documentation

From README.md and USAGE_GUIDE.md:

1. **Schema design:** Be specific about data types and units (e.g., "mortality_rate_percent" not just "mortality")
2. **Batch processing:** Process 5-10 papers at a time for manageable review
3. **Manual verification:** Always verify a sample of extractions against source papers
4. **PDF requirements:** PDFs must contain extractable text (not scanned images)
5. **Citation verification:** Check that `citations` are enabled and response includes citation objects

## Troubleshooting

**Missing citations:**
- Verify `extra_body={"citations": {"enabled": True}}` in API call
- Check that data actually exists in source document
- Review extraction prompt specificity

**JSON parsing errors:**
- Ensure prompt explicitly requests JSON-only output
- Add error handling with fallback parsing
- Check for malformed responses from API

**PDF extraction issues:**
- Confirm PDFs contain text (not images)
- Check page numbers match paper numbering
- Use OCR preprocessing if needed for scanned papers (e.g., using `pytesseract` or `easyocr`).

**Zero-cell problems:**
- Continuity correction (0.5) is automatically applied
- Verify input data has non-zero denominators
- Check for studies with extreme effect sizes (may indicate data issues)
