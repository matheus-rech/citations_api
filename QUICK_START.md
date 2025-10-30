# 🚀 Quick Start: Meta-Analysis with Citations API

## What You've Got

A complete toolkit for extracting data from research papers and performing meta-analysis with **full citation provenance**. Every extracted number is linked to its exact source in the paper.

## 📦 Files Included

```
meta_analysis_citations_api/
│
├── 📘 Documentation
│   ├── README.md              ← Start here! Complete overview
│   ├── USAGE_GUIDE.md         ← Detailed examples and scenarios
│   └── QUICK_START.md         ← This file
│
├── 🔧 Core Tools
│   ├── meta_analysis_extractor.py     ← Extract data from PDFs with citations
│   ├── meta_analysis_calculator.py    ← Calculate effect sizes & meta-analysis
│   ├── streaming_extractor.py         ← Real-time progress tracking
│   └── complete_workflow.py           ← End-to-end automated workflow
│
├── 💡 Examples
│   └── minimal_example.py             ← Simplest working example
│
└── 📋 Setup
    └── requirements.txt               ← Python dependencies
```

## ⚡ 5-Minute Quick Start

### 1. Install
```bash
pip install anthropic pandas numpy
export ANTHROPIC_API_KEY='your-key-here'
```

### 2. Run Minimal Example
```bash
python minimal_example.py
```

This demonstrates the core concept with a single paper.

### 3. Run Full Workflow
```python
from complete_workflow import CompleteMetaAnalysisWorkflow

workflow = CompleteMetaAnalysisWorkflow()

papers = ["study1.pdf", "study2.pdf", "study3.pdf"]

workflow.run_complete_workflow(
    pdf_paths=papers,
    study_type="clinical_trial",  # or "surgical", "observational"
    output_dir="./my_analysis"
)
```

You'll get:
- ✅ Extracted data in JSON and CSV
- ✅ Complete citation map
- ✅ Meta-analysis results (fixed & random effects)
- ✅ Professional HTML report

## 🎯 Key Features

### Full Citation Provenance
```python
# Every extracted value comes with citations
{
  "mortality_intervention": 15,
  "citations": [
    {
      "cited_text": "15 deaths occurred in the SDC group",
      "page": 8
    }
  ]
}
```

### Multiple Study Types
- **Clinical Trials**: RCTs, quasi-RCTs
- **Surgical Studies**: SDC, cerebellar necrosectomy, etc.
- **Observational**: Cohort, case-control

### Statistical Analysis
- Odds ratios (OR)
- Risk ratios (RR)
- Standardized mean differences (SMD)
- Fixed-effect meta-analysis
- Random-effects meta-analysis (DerSimonian-Laird)
- Heterogeneity assessment (Q, I², τ²)

## 📊 Real-World Use Case

### Cerebellar Stroke Meta-Analysis

```python
# Your papers
papers = [
    "jauss_1999.pdf",
    "raco_2003.pdf",
    "pfefferkorn_2009.pdf"
]

# Run workflow
workflow.run_complete_workflow(
    pdf_paths=papers,
    study_type="surgical",
    output_dir="./cerebellar_sdc"
)
```

**Output:**
```
STEP 1: DATA EXTRACTION WITH CITATIONS
✓ 3/3 papers processed successfully
✓ 42 total citations tracked

STEP 2: EFFECT SIZE CALCULATION
✓ 3 studies with complete data

STEP 3: META-ANALYSIS
Pooled OR: 0.398 [0.231, 0.687]
I²: 52.7% (moderate heterogeneity)
p = 0.0016 (significant)

STEP 4: REPORT GENERATION
✓ Report: ./cerebellar_sdc/FINAL_META_ANALYSIS_REPORT.html
```

## 🔄 Typical Workflow

```
1. Define Papers
   ↓
2. Choose Study Type
   ↓
3. Run Extraction → Citations tracked automatically
   ↓
4. Calculate Effect Sizes → From extracted data
   ↓
5. Meta-Analysis → Pooled estimates
   ↓
6. Generate Report → Ready for publication
```

## 🎨 Customization Examples

### Custom Schema
```python
my_schema = {
    "intervention": {
        "drug_name": "string",
        "dose_mg": "float"
    },
    "outcomes": {
        "response_rate_treatment": "float (percentage)",
        "response_rate_placebo": "float (percentage)"
    }
}
```

### Streaming with Progress
```python
from streaming_extractor import StreamingMetaAnalysisExtractor

extractor = StreamingMetaAnalysisExtractor()

def on_citation(citation):
    print(f"📌 Found citation on page {citation['start_page_number']}")

result = extractor.extract_with_streaming(
    "paper.pdf",
    schema,
    on_citation_callback=on_citation
)
```

## 📈 What Makes This Different?

### Traditional Approach ❌
```
1. Read paper manually
2. Copy numbers into spreadsheet
3. No record of where numbers came from
4. Hard to verify during peer review
5. Error-prone
```

### With Citations API ✅
```
1. AI extracts data automatically
2. Every number linked to source text & page
3. Complete audit trail
4. Easy verification
5. Reproducible
```

## 🔍 Example Output

### Extraction Result
```json
{
  "document_title": "Smith_2023.pdf",
  "extracted_data": {
    "participants": {
      "sample_size": 150,
      "mean_age": 65.5
    },
    "outcomes": {
      "mortality_intervention": 10,
      "mortality_control": 25
    }
  },
  "citations": [
    {
      "cited_text": "A total of 150 patients were enrolled between 2020 and 2022",
      "start_page_number": 3,
      "end_page_number": 4
    },
    {
      "cited_text": "Mortality was 10 (20%) in the intervention group and 25 (50%) in the control group",
      "start_page_number": 8,
      "end_page_number": 9
    }
  ]
}
```

### Meta-Analysis Result
```
Random-Effects Model:
  Pooled OR: 0.398 [95% CI: 0.231-0.687]
  Z = -3.156, p = 0.0016
  
Heterogeneity:
  Q = 8.45 (df=4), p = 0.0763
  I² = 52.7% (moderate)
  τ² = 0.1234
  
Interpretation:
  ✓ Significant effect (p < 0.05)
  ⚠️ Moderate heterogeneity
  → Random-effects model recommended
```

## 🛠️ Common Tasks

### Task 1: Extract from Single Paper
```bash
python minimal_example.py
```

### Task 2: Batch Process Multiple Papers
```python
from meta_analysis_extractor import MetaAnalysisExtractor

extractor = MetaAnalysisExtractor()
results = extractor.extract_from_multiple_papers(papers, schema)
extractor.save_results(results, output_dir="./output")
```

### Task 3: Generate HTML Report
```python
from streaming_extractor import StreamingMetaAnalysisExtractor

extractor = StreamingMetaAnalysisExtractor()
extractor.generate_citation_report(results, "report.html")
```

### Task 4: Full Meta-Analysis Pipeline
```python
from complete_workflow import CompleteMetaAnalysisWorkflow

workflow = CompleteMetaAnalysisWorkflow()
workflow.run_complete_workflow(papers, "clinical_trial", "./output")
```

## 📚 Where to Go Next

1. **Read README.md** for complete feature overview
2. **Check USAGE_GUIDE.md** for detailed scenarios
3. **Run minimal_example.py** to see it in action
4. **Modify schemas** for your research domain
5. **Process your own papers!**

## 💡 Pro Tips

1. **Start small**: Test on 2-3 papers first
2. **Customize schemas**: Make them specific to your study type
3. **Check citations**: Verify a sample manually
4. **Version your work**: Keep extraction logs
5. **Validate results**: Use built-in validation functions

## ⚠️ Important Notes

- Requires Anthropic API key
- Works best with text-based PDFs (not scanned images)
- Citations are tracked at sentence level for PDFs
- Always verify a sample of extractions manually
- Suitable for systematic reviews and meta-analyses

## 🎓 Learn More

- [Anthropic API Docs](https://docs.anthropic.com)
- [Citations Feature](https://docs.anthropic.com/en/docs/build-with-claude/citations)
- [PDF Support](https://docs.anthropic.com/en/docs/build-with-claude/pdf-support)

## 🤝 Need Help?

1. Check USAGE_GUIDE.md troubleshooting section
2. Review example outputs
3. Adjust schema specificity
4. Try different prompt formulations

---

**Ready to start?** → `python minimal_example.py`

**Got papers ready?** → `python complete_workflow.py`

**Want full docs?** → Open `README.md`

---

Built with ❤️ using Anthropic's Claude and Citations API
