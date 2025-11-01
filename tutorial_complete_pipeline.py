#!/usr/bin/env python3
"""
Complete Tutorial: 4-Step Pipeline for Systematic Reviews with Citation Provenance

This tutorial shows you how to run the complete meta-analysis workflow from
PDF extraction to publication-ready reports with full citation tracking.
"""

# ============================================================================
# STEP-BY-STEP GUIDE: Running the Complete 4-Step Pipeline
# ============================================================================

"""
OVERVIEW:
---------
The 4-step pipeline automates systematic review meta-analysis:

  STEP 1: Data Extraction    → Extract structured data from PDF papers
  STEP 2: Effect Sizes        → Calculate OR/RR/SMD with confidence intervals
  STEP 3: Meta-Analysis       → Fixed-effect and random-effects pooling
  STEP 4: Report Generation   → HTML report with clickable citations


PREREQUISITES:
--------------
1. Install dependencies:
   pip install anthropic pandas numpy

2. Set API key:
   export ANTHROPIC_API_KEY='your-anthropic-api-key-here'

3. Prepare your PDF papers (research articles for your systematic review)
"""

# ============================================================================
# METHOD 1: AUTOMATIC - Run Complete Workflow (Recommended)
# ============================================================================

def method1_automatic_workflow():
    """
    Run all 4 steps automatically with a single function call.
    This is the easiest way to get started.
    """

    from complete_workflow import CompleteMetaAnalysisWorkflow

    # Initialize the workflow
    workflow = CompleteMetaAnalysisWorkflow()

    # Define your PDF papers
    pdf_papers = [
        "papers/smith2023.pdf",         # Study 1
        "papers/johnson2022.pdf",       # Study 2
        "papers/wang2021.pdf",          # Study 3
        "papers/martinez2020.pdf",      # Study 4
    ]

    # Run the complete 4-step pipeline
    workflow.run_complete_workflow(
        pdf_paths=pdf_papers,
        study_type="clinical_trial",    # Options: "clinical_trial", "surgical", "observational"
        output_dir="./my_meta_analysis"
    )

    print("\n✅ Complete! Check './my_meta_analysis' for all outputs.")


# ============================================================================
# METHOD 2: STEP-BY-STEP - Run Each Step Individually (More Control)
# ============================================================================

def method2_step_by_step():
    """
    Run each step individually for more control and customization.
    Useful if you need to inspect or modify data between steps.
    """

    from complete_workflow import CompleteMetaAnalysisWorkflow

    # Initialize
    workflow = CompleteMetaAnalysisWorkflow()

    pdf_papers = [
        "papers/smith2023.pdf",
        "papers/johnson2022.pdf",
        "papers/wang2021.pdf",
    ]

    output_dir = "./my_meta_analysis"

    # ─────────────────────────────────────────────────────────────────────
    # STEP 1: Extract Data from PDFs
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("STEP 1: EXTRACTING DATA FROM PDFs")
    print("="*70)

    extraction_results = workflow.step1_extract_data(
        pdf_paths=pdf_papers,
        study_type="clinical_trial",
        output_dir=output_dir
    )

    # Inspect extraction results
    print(f"\n✓ Extracted data from {len(extraction_results)} papers")
    print(f"✓ Total citations tracked: {sum(r.get('citation_count', 0) for r in extraction_results)}")

    # You can inspect the extracted data here if needed
    for result in extraction_results:
        print(f"\n  Study: {result.get('study_id', 'Unknown')}")
        print(f"    - Sample size: {result.get('extracted_data', {}).get('participants', {}).get('total_sample_size', 'N/A')}")
        print(f"    - Citations: {result.get('citation_count', 0)}")

    # ─────────────────────────────────────────────────────────────────────
    # STEP 2: Calculate Effect Sizes
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("STEP 2: CALCULATING EFFECT SIZES")
    print("="*70)

    calculator = workflow.step2_calculate_effect_sizes(output_dir=output_dir)

    print("\n✓ Effect sizes calculated for all studies")

    # ─────────────────────────────────────────────────────────────────────
    # STEP 3: Perform Meta-Analysis
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("STEP 3: PERFORMING META-ANALYSIS")
    print("="*70)

    meta_results = workflow.step3_meta_analysis(output_dir=output_dir)

    print("\n✓ Meta-analysis complete:")
    print(f"  - Fixed-effect pooled OR: {meta_results.get('fixed_effect', {}).get('pooled_effect', 'N/A')}")
    print(f"  - Random-effects pooled OR: {meta_results.get('random_effects', {}).get('pooled_effect', 'N/A')}")
    print(f"  - I² heterogeneity: {meta_results.get('random_effects', {}).get('heterogeneity', {}).get('i_squared', 'N/A')}%")

    # ─────────────────────────────────────────────────────────────────────
    # STEP 4: Generate HTML Report
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("STEP 4: GENERATING REPORT")
    print("="*70)

    report_path = workflow.step4_generate_report(
        output_dir=output_dir,
        include_forest_plot=True
    )

    print(f"\n✅ Report generated: {report_path}")
    print("\n✅ Complete workflow finished!")


# ============================================================================
# METHOD 3: CUSTOM - Customize Extraction Schema
# ============================================================================

def method3_custom_schema():
    """
    Create a custom extraction schema for your specific research domain.
    Example: Cerebellar stroke studies
    """

    from complete_workflow import CompleteMetaAnalysisWorkflow
    from meta_analysis_extractor import MetaAnalysisExtractor

    # Initialize
    workflow = CompleteMetaAnalysisWorkflow()

    # Define a custom schema for your specific research question
    custom_schema = {
        "study_info": {
            "first_author": "string - last name",
            "year": "integer",
            "journal": "string",
            "country": "string"
        },

        "patient_characteristics": {
            "total_patients": "integer",
            "mean_age": "float - years",
            "percent_male": "float - percentage",
            "stroke_location": "string - cerebellar/brainstem/other",
            "mean_infarct_volume": "float - mL"
        },

        "intervention_details": {
            "surgical_procedure": "string - SDC, EVD, necrosectomy",
            "timing_from_onset": "float - hours",
            "conservative_treatment": "string - medical management details"
        },

        "outcomes": {
            "mortality_surgical": "integer - deaths in surgical group",
            "mortality_conservative": "integer - deaths in conservative group",
            "favorable_outcome_surgical": "integer - mRS 0-3 in surgical",
            "favorable_outcome_conservative": "integer - mRS 0-3 in conservative",
            "mean_icu_stay_surgical": "float - days",
            "mean_icu_stay_conservative": "float - days"
        },

        "complications": {
            "rebleeding_surgical": "integer",
            "rebleeding_conservative": "integer",
            "hydrocephalus_surgical": "integer",
            "hydrocephalus_conservative": "integer"
        }
    }

    pdf_papers = [
        "papers/cerebellar_study1.pdf",
        "papers/cerebellar_study2.pdf",
        "papers/cerebellar_study3.pdf",
    ]

    # Use the extractor directly with custom schema
    extractor = MetaAnalysisExtractor()

    print("\n" + "="*70)
    print("EXTRACTING WITH CUSTOM SCHEMA")
    print("="*70)

    results = extractor.extract_from_multiple_papers(
        pdf_paths=pdf_papers,
        extraction_schema=custom_schema
    )

    # Save results
    extractor.save_results(
        results,
        output_dir="./custom_extraction",
        prefix="cerebellar_stroke"
    )

    print(f"\n✅ Custom extraction complete!")
    print(f"   - Extracted from {len(results)} papers")
    print(f"   - Using custom schema with {len(custom_schema)} categories")
    print("   - Results saved to './custom_extraction'")


# ============================================================================
# METHOD 4: ADVANCED - Use Streaming for Progress Feedback
# ============================================================================

def method4_streaming():
    """
    Use streaming extraction for real-time progress updates.
    Useful for long papers or when you want to monitor progress.
    """

    from streaming_extractor import StreamingMetaAnalysisExtractor

    extractor = StreamingMetaAnalysisExtractor()

    # Define callbacks for progress tracking
    def on_text_chunk(text):
        """Called when text is received"""
        print(text, end='', flush=True)

    def on_citation_found(citation):
        """Called when a citation is found"""
        page = citation.get('start_page_number', '?')
        print(f"\n  [📎 Citation found on page {page}]", flush=True)

    # Define schema
    schema = {
        "study_info": {"first_author": "string", "year": "integer"},
        "participants": {"total_sample_size": "integer"},
        "outcomes": {
            "mortality_intervention": "integer",
            "mortality_control": "integer"
        }
    }

    print("\n" + "="*70)
    print("STREAMING EXTRACTION (Real-time Progress)")
    print("="*70)

    result = extractor.extract_with_streaming(
        pdf_path="papers/study1.pdf",
        schema=schema,
        on_text_callback=on_text_chunk,
        on_citation_callback=on_citation_found
    )

    print(f"\n\n✅ Streaming extraction complete!")
    print(f"   - Citations found: {result.get('citation_count', 0)}")


# ============================================================================
# OUTPUT FILES EXPLAINED
# ============================================================================

"""
After running the workflow, you'll get these output files:

my_meta_analysis/
├── step1_extraction_complete.json
│   └─ Raw extraction data with full citation objects
│      Contains: study_id, extracted_data, citations, citation_count
│
├── step1_extraction_data.csv
│   └─ Tabular format for Excel/R/SPSS
│      Easy to import and review
│
├── step1_extraction_citations.json
│   └─ Citation map linking data points to sources
│      Format: {"study_id": [{"page": X, "text": "..."}]}
│
├── step3_meta_analysis_results.json
│   └─ Statistical results
│      Contains:
│        - Fixed-effect pooled estimates
│        - Random-effects pooled estimates
│        - Heterogeneity statistics (Q, I², τ²)
│        - Individual study effect sizes
│
└── FINAL_META_ANALYSIS_REPORT.html
    └─ Interactive HTML report with:
        - Summary statistics
        - Forest plot data
        - Individual study details
        - Clickable citations
        - Publication-ready formatting
"""


# ============================================================================
# STUDY TYPE OPTIONS
# ============================================================================

"""
Choose the appropriate study type for your meta-analysis:

1. "clinical_trial"
   ─────────────────
   For: RCTs, quasi-RCTs, controlled trials
   Extracts:
     - Study design and methodology
     - Sample sizes by arm
     - Baseline characteristics
     - Primary/secondary outcomes
     - Effect estimates and CIs
     - Risk of bias assessment

2. "surgical"
   ───────────
   For: Surgical intervention studies
   Extracts:
     - Surgical procedures
     - Operative details (time, blood loss)
     - Mortality rates
     - Functional outcomes (mRS, GOS)
     - Complications
     - Hospital/ICU stay

3. "observational"
   ────────────────
   For: Cohort studies, case-control studies
   Extracts:
     - Exposure definitions
     - Outcome measures
     - Adjusted/unadjusted estimates
     - Confounders
     - Follow-up duration
"""


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Run different methods based on your needs
    """

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║         Complete Tutorial: 4-Step Meta-Analysis Pipeline             ║
║              with Citation Provenance Tracking                       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Choose a method to run:

1. AUTOMATIC    → Run complete 4-step workflow (easiest)
2. STEP-BY-STEP → Run each step individually (more control)
3. CUSTOM       → Use custom extraction schema
4. STREAMING    → Real-time progress updates

Uncomment the method you want to try below.
    """)

    # Uncomment the method you want to run:

    # method1_automatic_workflow()      # Recommended for beginners
    # method2_step_by_step()            # For more control
    # method3_custom_schema()           # For custom research domains
    # method4_streaming()               # For progress monitoring

    print("""
═══════════════════════════════════════════════════════════════════════

📚 NEXT STEPS:

1. Choose a method above and uncomment it
2. Update the PDF file paths to your actual papers
3. Set your ANTHROPIC_API_KEY environment variable
4. Run: python tutorial_complete_pipeline.py

═══════════════════════════════════════════════════════════════════════

💡 TIPS:

- Start with method1_automatic_workflow() for simplicity
- Use method2_step_by_step() to inspect data between steps
- Create custom schemas (method3) for specialized research domains
- Use method4_streaming() for long documents

═══════════════════════════════════════════════════════════════════════

📖 Documentation:
   • CLAUDE.md - Developer guidance and architecture
   • README.md - Feature overview
   • QUICK_START.md - 5-minute tutorial
   • USAGE_GUIDE.md - Advanced patterns

═══════════════════════════════════════════════════════════════════════
    """)


if __name__ == "__main__":
    main()
