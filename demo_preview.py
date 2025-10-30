#!/usr/bin/env python3
"""
Demo Preview - Shows what the Meta-Analysis toolkit produces
This demo simulates the output without requiring PDFs or API calls
"""

import json
from datetime import datetime


def print_header(title):
    print("\n" + "="*70)
    print(title.center(70))
    print("="*70)


def demo_minimal_extraction():
    """Simulate minimal example output"""
    print_header("STEP 1: DATA EXTRACTION WITH CITATIONS")

    print("\n📄 Processing: sample_research_paper.pdf")
    print("🔄 Sending request to Claude API...")
    print("✓ Response received\n")

    # Simulated extraction result
    extracted_data = {
        "first_author": "Smith",
        "year": 2023,
        "sample_size": 150,
        "deaths_intervention": 15,
        "deaths_control": 28
    }

    print("📊 Extracted Data:")
    print(json.dumps(extracted_data, indent=2))

    # Simulated citations
    citations = [
        {
            "page": 1,
            "text": "Smith et al. published their findings in 2023...",
            "field": "first_author, year"
        },
        {
            "page": 5,
            "text": "A total of 150 patients were enrolled in the study between 2020 and 2022.",
            "field": "sample_size"
        },
        {
            "page": 12,
            "text": "Table 2 shows mortality outcomes: 15 deaths occurred in the surgical decompression group",
            "field": "deaths_intervention"
        },
        {
            "page": 12,
            "text": "while 28 deaths were recorded in the conservative treatment group",
            "field": "deaths_control"
        }
    ]

    print_header("CITATIONS (Evidence Tracking)")
    print(f"\n✅ Found {len(citations)} citations linking data to sources:\n")

    for i, citation in enumerate(citations, 1):
        print(f"{i}. Page {citation['page']} → [{citation['field']}]")
        print(f"   \"{citation['text']}\"")
        print()


def demo_effect_size_calculation():
    """Simulate effect size calculation"""
    print_header("STEP 2: EFFECT SIZE CALCULATION")

    print("\n📐 Calculating Odds Ratio (OR) for mortality:")
    print("\nIntervention group: 15/75 died")
    print("Control group: 28/75 died")

    # Simulated calculation
    result = {
        "odds_ratio": 0.45,
        "log_or": -0.798,
        "standard_error": 0.325,
        "95_ci_lower": 0.24,
        "95_ci_upper": 0.85,
        "p_value": 0.014
    }

    print("\n✓ Results:")
    print(f"  OR = {result['odds_ratio']:.2f}")
    print(f"  95% CI: [{result['95_ci_lower']:.2f}, {result['95_ci_upper']:.2f}]")
    print(f"  p = {result['p_value']:.3f}")
    print(f"\n  → Intervention reduces odds of death by 55%")

    print("\n📊 With citations preserved:")
    print("  ├─ OR: 0.45 → Traced to Table 2, page 12")
    print("  ├─ Deaths (intervention): 15 → Page 12, cited text")
    print("  └─ Deaths (control): 28 → Page 12, cited text")


def demo_multi_study_meta_analysis():
    """Simulate meta-analysis across multiple studies"""
    print_header("STEP 3: META-ANALYSIS (Multiple Studies)")

    studies = [
        {"author": "Smith 2023", "or": 0.45, "ci_lower": 0.24, "ci_upper": 0.85, "weight": 28.3},
        {"author": "Johnson 2022", "or": 0.52, "ci_lower": 0.31, "ci_upper": 0.87, "weight": 31.2},
        {"author": "Wang 2021", "or": 0.38, "ci_lower": 0.18, "ci_upper": 0.79, "weight": 22.5},
        {"author": "Martinez 2020", "or": 0.61, "ci_lower": 0.28, "ci_upper": 1.33, "weight": 18.0}
    ]

    print("\n📚 Included Studies:")
    for study in studies:
        print(f"  • {study['author']:<20} OR: {study['or']:.2f} [{study['ci_lower']:.2f}-{study['ci_upper']:.2f}]  Weight: {study['weight']:.1f}%")

    print("\n🔬 Statistical Analysis:")
    print("\n  Fixed-Effect Model:")
    print("    Pooled OR: 0.49 [0.36-0.67]")
    print("    Z = -4.23, p < 0.001")

    print("\n  Random-Effects Model (DerSimonian-Laird):")
    print("    Pooled OR: 0.48 [0.34-0.68]")
    print("    Z = -4.01, p < 0.001")

    print("\n  Heterogeneity Assessment:")
    print("    Q = 1.87 (p = 0.600)")
    print("    I² = 0.0% (no heterogeneity)")
    print("    τ² = 0.000")

    print("\n  ✓ Low heterogeneity → Fixed-effect model appropriate")
    print("  ✓ Intervention reduces mortality by ~51%")


def demo_output_files():
    """Show what output files are generated"""
    print_header("STEP 4: REPORT GENERATION")

    print("\n📁 Output Directory Structure:")
    print("""
  meta_analysis_results/
  ├── step1_extraction_complete.json        (2.4 KB)
  │   └─ Raw extraction data with full citation objects
  │
  ├── step1_extraction_data.csv             (1.1 KB)
  │   └─ Tabular format for Excel/spreadsheets
  │
  ├── step1_extraction_citations.json       (3.8 KB)
  │   └─ Citation map linking each data point to source
  │
  ├── step3_meta_analysis_results.json      (1.9 KB)
  │   └─ Statistical results (OR, CI, heterogeneity)
  │
  └── FINAL_META_ANALYSIS_REPORT.html       (15.2 KB)
      └─ Interactive report with:
          • Forest plot data
          • Heterogeneity statistics
          • Clickable citations linking to source pages
          • Publication-ready tables
    """)


def demo_citation_audit_trail():
    """Show citation provenance example"""
    print_header("CITATION AUDIT TRAIL")

    print("\n🔍 Complete Provenance Tracking:\n")

    print("Data Point: Mortality in Intervention Group = 15")
    print("    ↓")
    print("  Citation Chain:")
    print("    1️⃣  Source Paper: Smith et al. 2023")
    print("        📄 File: cerebellar_stroke_rct.pdf")
    print("    2️⃣  Location: Page 12, Table 2")
    print("        📝 Exact text: \"15 deaths occurred in the surgical")
    print("           decompression group (20% mortality)\"")
    print("    3️⃣  Used in calculation:")
    print("        📊 Effect Size: OR = 0.45 [0.24-0.85]")
    print("    4️⃣  Included in meta-analysis:")
    print("        📈 Pooled OR = 0.49 [0.36-0.67]")

    print("\n✅ Benefits:")
    print("   • Verify any data point instantly")
    print("   • Complete audit trail for peer review")
    print("   • PRISMA-compliant systematic review")
    print("   • Reproducible research")


def show_html_report_preview():
    """Show what the HTML report looks like"""
    print_header("HTML REPORT PREVIEW")

    print("""
╔════════════════════════════════════════════════════════════════════╗
║                   Meta-Analysis Report                              ║
║           Surgical Decompression vs Conservative Treatment          ║
╚════════════════════════════════════════════════════════════════════╝

📊 Summary Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Studies included:        4
  Total participants:      600
  Citations tracked:       48

  Pooled OR (Random):      0.48 [0.34-0.68]
  P-value:                 < 0.001

  Heterogeneity (I²):      0.0%
  Interpretation:          Low heterogeneity

🎯 Forest Plot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Study              OR [95% CI]         Weight    ——————○——————
Smith 2023         0.45 [0.24-0.85]    28.3%           ◆
Johnson 2022       0.52 [0.31-0.87]    31.2%           ◆
Wang 2021          0.38 [0.18-0.79]    22.5%         ◆
Martinez 2020      0.61 [0.28-1.33]    18.0%           ◆
                                              0.5  1.0  2.0
Pooled             0.48 [0.34-0.68]   100.0%          ◇
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                         Favours    Favours
                                       Intervention Control

📖 Individual Study Details (with citations)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 Smith 2023
   Sample size: 150 [Citation: Page 5]
   Deaths (Intervention): 15 [Citation: Page 12, Table 2]
   Deaths (Control): 28 [Citation: Page 12, Table 2]
   OR: 0.45 [0.24-0.85]

   → Click any citation to see exact source text

📄 Johnson 2022
   Sample size: 180 [Citation: Page 3]
   Deaths (Intervention): 18 [Citation: Page 9, Figure 2]
   Deaths (Control): 32 [Citation: Page 9, Figure 2]
   OR: 0.52 [0.31-0.87]

[... continued for all studies ...]

🔬 Interpretation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Surgical decompression is associated with a 52% reduction in odds
of mortality compared to conservative treatment (OR 0.48, 95% CI
0.34-0.68, p < 0.001). Heterogeneity is low (I² = 0%), suggesting
consistent treatment effects across studies.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated: {}
Tool: Meta-Analysis Toolkit with Citations API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║        Meta-Analysis Toolkit with Citations API                      ║
║                     DEMO PREVIEW                                      ║
║                                                                      ║
║  This demonstrates what the toolkit produces when you run it         ║
║  with real research papers.                                          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Run demos
    demo_minimal_extraction()
    demo_effect_size_calculation()
    demo_multi_study_meta_analysis()
    demo_output_files()
    demo_citation_audit_trail()
    show_html_report_preview()

    # Summary
    print_header("WHAT MAKES THIS POWERFUL")
    print("""
🎯 Key Features Demonstrated:

1. Automatic Data Extraction
   ├─ Extracts structured data from PDF papers using AI
   ├─ Custom schemas for different study types
   └─ Handles complex tables and nested data

2. Citation Tracking
   ├─ Every number linked to exact source location
   ├─ Page numbers and quoted text preserved
   └─ Complete audit trail for verification

3. Statistical Analysis
   ├─ Effect sizes: OR, RR, SMD with confidence intervals
   ├─ Meta-analysis: Fixed and random effects models
   └─ Heterogeneity assessment: Q, I², τ²

4. Publication-Ready Output
   ├─ JSON for programmatic access
   ├─ CSV for spreadsheets
   └─ HTML with interactive citations

💡 Real-World Impact:

  Without this toolkit:
    ❌ Manual data extraction (days of work)
    ❌ Prone to transcription errors
    ❌ No citation tracking
    ❌ Difficult to verify during peer review

  With this toolkit:
    ✅ Automated extraction (minutes per paper)
    ✅ AI-powered accuracy with verification
    ✅ Complete citation provenance
    ✅ Transparent, reproducible research
    """)

    print_header("NEXT STEPS TO RUN IT YOURSELF")
    print("""
To run with your own research papers:

1. Install dependencies:
   pip install -r requirements.txt

2. Set your API key:
   export ANTHROPIC_API_KEY='your-key'

3. Run examples:
   # Single paper extraction
   python minimal_example.py

   # Complete workflow (extraction → meta-analysis → report)
   python complete_workflow.py

   # Streaming with progress
   python streaming_extractor.py

4. Customize schemas:
   Edit schemas in complete_workflow.py or create your own
   for specific research domains (e.g., cardiology, oncology)

📚 Documentation:
   • README.md - Full feature overview
   • QUICK_START.md - 5-minute tutorial
   • USAGE_GUIDE.md - Advanced patterns
   • CLAUDE.md - Developer guidance
    """)

    print("\n" + "="*70)
    print("Demo complete! Ready to extract data from real papers.".center(70))
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
