# Quick Reference: 4-Step Pipeline for Systematic Reviews

## Setup (One-Time)

```bash
# Install dependencies
pip install anthropic pandas numpy

# Set API key
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Method 1: Automatic (Recommended)

**Run all 4 steps with one command:**

```python
from complete_workflow import CompleteMetaAnalysisWorkflow

# Initialize
workflow = CompleteMetaAnalysisWorkflow()

# Run complete pipeline
workflow.run_complete_workflow(
    pdf_paths=[
        "papers/smith2023.pdf",
        "papers/johnson2022.pdf",
        "papers/wang2021.pdf"
    ],
    study_type="clinical_trial",  # or "surgical", "observational"
    output_dir="./my_meta_analysis"
)
```

**That's it!** The workflow will:
- ✅ Extract data from PDFs with citations
- ✅ Calculate effect sizes (OR/RR/SMD)
- ✅ Perform meta-analysis (fixed + random effects)
- ✅ Generate HTML report with forest plot

---

## Method 2: Step-by-Step (More Control)

**Run each step individually:**

```python
from complete_workflow import CompleteMetaAnalysisWorkflow

workflow = CompleteMetaAnalysisWorkflow()

pdfs = ["paper1.pdf", "paper2.pdf", "paper3.pdf"]
output = "./results"

# Step 1: Extract data
workflow.step1_extract_data(pdfs, "clinical_trial", output)

# Step 2: Calculate effect sizes
workflow.step2_calculate_effect_sizes(output)

# Step 3: Meta-analysis
workflow.step3_meta_analysis(output)

# Step 4: Generate report
workflow.step4_generate_report(output)
```

---

## Method 3: Custom Schema

**For specialized research domains:**

```python
from meta_analysis_extractor import MetaAnalysisExtractor

# Define custom schema
custom_schema = {
    "study_info": {
        "first_author": "string",
        "year": "integer"
    },
    "participants": {
        "total_patients": "integer",
        "mean_age": "float"
    },
    "outcomes": {
        "mortality_intervention": "integer",
        "mortality_control": "integer"
    }
}

# Extract with custom schema
extractor = MetaAnalysisExtractor()
results = extractor.extract_from_multiple_papers(
    pdf_paths=["paper1.pdf", "paper2.pdf"],
    extraction_schema=custom_schema
)

# Save results
extractor.save_results(results, output_dir="./custom_results")
```

---

## Method 4: Streaming (Real-Time Progress)

**For long documents with progress feedback:**

```python
from streaming_extractor import StreamingMetaAnalysisExtractor

extractor = StreamingMetaAnalysisExtractor()

# Define callbacks
def on_text(text):
    print(text, end='', flush=True)

def on_citation(citation):
    print(f"\n[Citation on page {citation['start_page_number']}]")

# Extract with streaming
result = extractor.extract_with_streaming(
    pdf_path="long_paper.pdf",
    schema=your_schema,
    on_text_callback=on_text,
    on_citation_callback=on_citation
)
```

---

## Study Type Options

| Study Type | Use For | Key Extractions |
|------------|---------|-----------------|
| `"clinical_trial"` | RCTs, controlled trials | Sample sizes, outcomes, risk of bias |
| `"surgical"` | Surgical interventions | Procedures, mortality, complications, mRS/GOS |
| `"observational"` | Cohort, case-control | Exposures, adjusted estimates, confounders |

---

## Output Files

After running the workflow, you get:

```
my_meta_analysis/
├── step1_extraction_complete.json     # Raw data + citations
├── step1_extraction_data.csv          # Tabular format
├── step1_extraction_citations.json    # Citation map
├── step3_meta_analysis_results.json   # Statistical results
└── FINAL_META_ANALYSIS_REPORT.html    # Publication-ready report
```

---

## Command-Line Examples

### Run minimal example (single paper)
```bash
python minimal_example.py
```

### Run complete workflow
```bash
python complete_workflow.py
```

### Run streaming extractor
```bash
python streaming_extractor.py
```

### Run demo preview (no PDFs needed)
```bash
python demo_preview.py
```

### Run tutorial
```bash
python tutorial_complete_pipeline.py
```

---

## Citation Tracking Example

Every extracted data point includes citations:

```json
{
  "study_id": "Smith2023",
  "extracted_data": {
    "participants": {
      "total_sample_size": 150
    },
    "outcomes": {
      "mortality_intervention": 15
    }
  },
  "citations": [
    {
      "type": "page_location",
      "cited_text": "A total of 150 patients were enrolled",
      "start_page_number": 5,
      "end_page_number": 5
    },
    {
      "type": "page_location",
      "cited_text": "15 deaths occurred in the surgical group",
      "start_page_number": 12,
      "end_page_number": 12
    }
  ],
  "citation_count": 12
}
```

---

## Statistical Methods

### Effect Sizes Calculated

**Odds Ratio (OR)** - For dichotomous outcomes
```python
calculator.calculate_odds_ratio(
    events_treatment=15,
    n_treatment=75,
    events_control=28,
    n_control=75
)
# Returns: (log_or, se, ci_lower, ci_upper)
```

**Risk Ratio (RR)** - For incidence data
```python
calculator.calculate_risk_ratio(
    events_treatment=15,
    n_treatment=75,
    events_control=28,
    n_control=75
)
```

**Standardized Mean Difference (SMD)** - For continuous outcomes (Hedges' g)
```python
calculator.calculate_standardized_mean_difference(
    mean_treatment=5.2,
    sd_treatment=1.3,
    n_treatment=50,
    mean_control=3.8,
    sd_control=1.1,
    n_control=50
)
```

### Meta-Analysis Models

**Fixed-Effect** - Assumes homogeneous effect
```python
fixed_results = calculator.perform_fixed_effect_meta_analysis()
```

**Random-Effects** - Accounts for heterogeneity (DerSimonian-Laird)
```python
random_results = calculator.perform_random_effects_meta_analysis()
```

**Heterogeneity Statistics:**
- Q-statistic (chi-square test)
- I² (percentage of variation due to heterogeneity)
- τ² (between-study variance)

---

## Troubleshooting

### PDFs not found
```python
# Use absolute paths
pdf_paths = [
    "/home/user/papers/study1.pdf",
    "/home/user/papers/study2.pdf"
]
```

### API key not set
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
# Or in Python:
workflow = CompleteMetaAnalysisWorkflow(api_key='sk-ant-...')
```

### Missing citations
Ensure citations are enabled in API call:
```python
extra_body={"citations": {"enabled": True}}
```

### JSON parsing errors
Check that your schema is properly formatted and the prompt requests JSON output.

---

## Best Practices

1. **Start small**: Test with 2-3 papers first
2. **Verify extraction**: Manually check sample of extracted data against PDFs
3. **Schema specificity**: Be explicit about data types and units
4. **Batch size**: Process 5-10 papers at a time for manageable review
5. **Citation verification**: Always review citation quality
6. **Version control**: Save extraction results for reproducibility

---

## Real-World Workflow

```bash
# 1. Setup
export ANTHROPIC_API_KEY='your-key'
mkdir -p papers results

# 2. Add your PDFs
cp ~/Downloads/*.pdf papers/

# 3. Create extraction script
cat > run_analysis.py << 'EOF'
from complete_workflow import CompleteMetaAnalysisWorkflow
import glob

workflow = CompleteMetaAnalysisWorkflow()
pdfs = glob.glob("papers/*.pdf")

workflow.run_complete_workflow(
    pdf_paths=pdfs,
    study_type="clinical_trial",
    output_dir="./results"
)
EOF

# 4. Run analysis
python run_analysis.py

# 5. Review results
open results/FINAL_META_ANALYSIS_REPORT.html
```

---

## Documentation

- **CLAUDE.md** - Architecture and developer guidance
- **README.md** - Complete feature overview
- **QUICK_START.md** - 5-minute getting started guide
- **USAGE_GUIDE.md** - Advanced patterns and troubleshooting
- **tutorial_complete_pipeline.py** - Interactive tutorial with examples

---

## Support

For issues or questions:
1. Check the documentation files above
2. Review example scripts (minimal_example.py, complete_workflow.py)
3. Run demo_preview.py to see expected output
4. Consult USAGE_GUIDE.md for troubleshooting

---

**Ready to start?** Run this:

```bash
python tutorial_complete_pipeline.py
```

This will guide you through all methods interactively!
