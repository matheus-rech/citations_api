"""
Complete Meta-Analysis Workflow with Anthropic Citations API
End-to-end: PDF extraction → Effect size calculation → Meta-analysis
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import anthropic

# Import our custom modules
from meta_analysis_extractor import MetaAnalysisExtractor
from meta_analysis_calculator import MetaAnalysisCalculator
from validation_poc import ValidationPipeline, ValidationReport

logger = logging.getLogger(__name__)


class CompleteMetaAnalysisWorkflow:
    """
    Complete workflow for conducting meta-analysis with full citation provenance
    """

    def __init__(self, api_key: str = None, enable_validation: bool = True):
        """
        Initialize workflow

        Args:
            api_key: Anthropic API key
            enable_validation: Enable automatic validation of extractions (recommended)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.extractor = MetaAnalysisExtractor(self.api_key)
        self.extraction_results = []
        self.calculator = None
        self.enable_validation = enable_validation

        if enable_validation:
            self.validator = ValidationPipeline()
            logger.info("Validation enabled - extractions will be automatically validated")
        else:
            self.validator = None
            logger.warning("Validation disabled - proceeding without quality checks")
    
    def define_extraction_schema(self, study_type: str = "clinical_trial") -> Dict[str, Any]:
        """
        Define extraction schema based on study type
        
        Args:
            study_type: Type of studies ("clinical_trial", "observational", "surgical")
        """
        
        if study_type == "clinical_trial":
            return {
                "study_identification": {
                    "first_author": "string - last name of first author",
                    "year": "integer - publication year",
                    "journal": "string - journal name",
                    "study_design": "string - RCT, quasi-RCT, etc.",
                    "country": "string - where study was conducted"
                },
                "participants": {
                    "total_sample_size": "integer - total number of participants",
                    "intervention_group_size": "integer - number in intervention group",
                    "control_group_size": "integer - number in control group",
                    "mean_age": "float - mean age in years",
                    "percent_male": "float - percentage of male participants",
                    "inclusion_criteria": "string - brief inclusion criteria",
                    "exclusion_criteria": "string - brief exclusion criteria"
                },
                "intervention": {
                    "intervention_name": "string - name of intervention",
                    "intervention_description": "string - brief description",
                    "control_name": "string - name of control",
                    "control_description": "string - brief description",
                    "follow_up_duration": "string - duration of follow-up"
                },
                "outcomes": {
                    "primary_outcome": "string - primary outcome measure",
                    "mortality_intervention": "integer - deaths in intervention group",
                    "mortality_control": "integer - deaths in control group",
                    "favorable_outcome_intervention": "integer - favorable outcomes in intervention",
                    "favorable_outcome_control": "integer - favorable outcomes in control",
                    "adverse_events_intervention": "integer - adverse events in intervention",
                    "adverse_events_control": "integer - adverse events in control"
                },
                "statistical_data": {
                    "effect_estimate": "float - reported effect size (OR, RR, HR, etc.)",
                    "confidence_interval_lower": "float - lower bound of 95% CI",
                    "confidence_interval_upper": "float - upper bound of 95% CI",
                    "p_value": "float - p-value for primary outcome",
                    "statistical_method": "string - statistical method used"
                },
                "quality_assessment": {
                    "randomization_method": "string - method of randomization",
                    "allocation_concealment": "string - adequate/inadequate/unclear",
                    "blinding": "string - who was blinded",
                    "incomplete_outcome_data": "string - how missing data handled",
                    "selective_reporting": "string - evidence of selective reporting",
                    "overall_risk_of_bias": "string - low/moderate/high"
                }
            }
        
        elif study_type == "surgical":
            return {
                "study_identification": {
                    "first_author": "string",
                    "year": "integer",
                    "journal": "string",
                    "study_design": "string",
                    "country": "string"
                },
                "participants": {
                    "total_patients": "integer",
                    "surgical_group_size": "integer",
                    "conservative_group_size": "integer",
                    "mean_age": "float",
                    "percent_male": "float",
                    "diagnosis": "string - primary diagnosis"
                },
                "intervention": {
                    "surgical_procedure": "string - type of surgery",
                    "surgical_approach": "string - approach used",
                    "timing_of_surgery": "string - when surgery performed",
                    "conservative_management": "string - conservative treatment details",
                    "follow_up_duration": "string"
                },
                "outcomes": {
                    "mortality_surgical": "integer - deaths in surgical group",
                    "mortality_conservative": "integer - deaths in conservative group",
                    "favorable_outcome_surgical": "integer - good functional outcome in surgical",
                    "favorable_outcome_conservative": "integer - good functional outcome in conservative",
                    "complications_surgical": "integer - complications in surgical group",
                    "complications_conservative": "integer - complications in conservative group",
                    "functional_outcome_measure": "string - scale used (mRS, GOS, etc.)"
                },
                "surgical_details": {
                    "mean_operative_time": "float - minutes",
                    "blood_loss": "float - mL",
                    "icu_stay": "float - days",
                    "hospital_stay": "float - days"
                }
            }
        
        else:  # observational
            return self.extractor._get_default_schema()
    
    def step1_extract_data(
        self,
        pdf_paths: List[str],
        study_type: str = "clinical_trial",
        output_dir: str = "./extraction_output"
    ) -> List[Dict[str, Any]]:
        """
        Step 1: Extract data from PDF papers with automatic validation
        """
        print("\n" + "="*70)
        print("STEP 1: DATA EXTRACTION WITH CITATIONS")
        print("="*70)

        # Define schema
        schema = self.define_extraction_schema(study_type)

        print(f"\nProcessing {len(pdf_paths)} papers...")
        print(f"Study type: {study_type}")
        print(f"Output directory: {output_dir}")
        if self.enable_validation:
            print("Validation: ENABLED (recommended)")
        else:
            print("Validation: DISABLED")

        # Extract data
        self.extraction_results = self.extractor.extract_from_multiple_papers(
            pdf_paths,
            extraction_schema=schema
        )

        # Validate extractions if enabled
        if self.enable_validation and self.validator:
            print("\n" + "-"*70)
            print("VALIDATING EXTRACTIONS")
            print("-"*70)

            validation_reports = []
            high_confidence_count = 0
            needs_review_count = 0
            needs_reextract_count = 0

            for result in self.extraction_results:
                if 'error' in result:
                    continue  # Skip failed extractions

                report = self.validator.validate_extraction(result)
                validation_reports.append(report)

                # Add validation info to result
                result['validation_report'] = {
                    'overall_confidence': report.overall_confidence,
                    'recommendation': report.recommendation,
                    'quality_issues': [
                        {'field': issue.field, 'severity': issue.severity, 'issue': issue.issue}
                        for issue in report.quality_issues
                    ],
                    'fields_requiring_review': report.fields_requiring_review
                }

                # Count recommendations
                if report.recommendation == 'accept':
                    high_confidence_count += 1
                elif report.recommendation == 'review':
                    needs_review_count += 1
                else:  # re-extract
                    needs_reextract_count += 1

                # Log warnings for low confidence
                if report.overall_confidence < 70:
                    logger.warning(
                        f"Low confidence extraction for {result.get('study_id', 'Unknown')}: "
                        f"{report.overall_confidence:.1f}%"
                    )

                # Log critical issues
                for issue in report.quality_issues:
                    if issue.severity == 'critical':
                        logger.error(
                            f"Critical issue in {result.get('study_id', 'Unknown')}: "
                            f"{issue.field} - {issue.issue}"
                        )

            # Print validation summary
            print(f"\n📊 Validation Summary:")
            print(f"   ✅ High confidence: {high_confidence_count} studies")
            print(f"   ⚠️  Needs review: {needs_review_count} studies")
            print(f"   🔴 Needs re-extraction: {needs_reextract_count} studies")

            if needs_reextract_count > 0:
                print(f"\n⚠️  WARNING: {needs_reextract_count} studies have critical quality issues")
                print("   Consider re-extracting these studies or manual verification")

            # Save validation reports
            validation_path = os.path.join(output_dir, "step1_validation_reports.json")
            with open(validation_path, 'w') as f:
                json.dump([
                    {
                        'study_id': r.study_id,
                        'overall_confidence': r.overall_confidence,
                        'recommendation': r.recommendation,
                        'quality_issues': [
                            {'field': i.field, 'severity': i.severity, 'issue': i.issue}
                            for i in r.quality_issues
                        ]
                    }
                    for r in validation_reports
                ], f, indent=2)
            print(f"\n💾 Validation reports saved to: {validation_path}")

        # Save results
        self.extractor.save_results(
            self.extraction_results,
            output_dir=output_dir,
            prefix="step1_extraction"
        )

        # Print summary
        successful = sum(1 for r in self.extraction_results if "error" not in r)
        total_citations = sum(r.get("citation_count", 0) for r in self.extraction_results)

        print(f"\n✅ Extraction complete:")
        print(f"   - {successful}/{len(pdf_paths)} papers processed successfully")
        print(f"   - {total_citations} total citations tracked")

        return self.extraction_results
    
    def step2_calculate_effect_sizes(
        self,
        output_dir: str = "./extraction_output"
    ) -> MetaAnalysisCalculator:
        """
        Step 2: Calculate effect sizes from extracted data
        """
        print("\n" + "="*70)
        print("STEP 2: EFFECT SIZE CALCULATION")
        print("="*70)
        
        if not self.extraction_results:
            raise ValueError("No extraction results available. Run step1_extract_data first.")
        
        # Initialize calculator
        self.calculator = MetaAnalysisCalculator(self.extraction_results)
        
        # Extract effect sizes
        print("\nCalculating effect sizes (odds ratios)...")
        effect_sizes = self.calculator.extract_dichotomous_outcomes()
        
        print(f"\n✅ Effect sizes calculated:")
        print(f"   - {len(effect_sizes)} studies with complete data")
        
        # Show individual effect sizes
        print("\nIndividual study results:")
        print("-" * 70)
        for es in effect_sizes:
            or_value = np.exp(es.effect_size)
            print(f"{es.study_id:30s} OR = {or_value:.3f} [{es.lower_ci:.3f}, {es.upper_ci:.3f}]")
        
        return self.calculator
    
    def step3_meta_analysis(
        self,
        output_dir: str = "./extraction_output"
    ) -> Dict[str, Any]:
        """
        Step 3: Perform meta-analysis
        """
        print("\n" + "="*70)
        print("STEP 3: META-ANALYSIS")
        print("="*70)
        
        if not self.calculator:
            raise ValueError("No calculator available. Run step2_calculate_effect_sizes first.")
        
        # Perform analyses
        print("\nPerforming fixed-effect meta-analysis...")
        fixed_results = self.calculator.perform_fixed_effect_meta_analysis()
        
        print("Performing random-effects meta-analysis...")
        random_results = self.calculator.perform_random_effects_meta_analysis()
        
        # Print summary
        self.calculator.print_summary(fixed_results, random_results)
        
        # Export results
        results = self.calculator.export_results(
            fixed_results,
            random_results,
            output_path=f"{output_dir}/step3_meta_analysis_results.json"
        )
        
        return results
    
    def step4_generate_report(
        self,
        output_dir: str = "./extraction_output",
        include_forest_plot: bool = True
    ):
        """
        Step 4: Generate comprehensive report
        """
        print("\n" + "="*70)
        print("STEP 4: REPORT GENERATION")
        print("="*70)
        
        report_path = f"{output_dir}/FINAL_META_ANALYSIS_REPORT.html"
        
        # Generate HTML report
        html = self._create_html_report(include_forest_plot)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ Report generated: {report_path}")
        print("\nWorkflow complete! All files saved to:", output_dir)
        
        return report_path
    
    def _create_html_report(self, include_forest_plot: bool = True) -> str:
        """Create comprehensive HTML report"""
        
        if not self.calculator:
            return "<html><body><h1>Error: No data available</h1></body></html>"
        
        # Get meta-analysis results
        fixed = self.calculator.perform_fixed_effect_meta_analysis()
        random = self.calculator.perform_random_effects_meta_analysis()
        forest_data = self.calculator.generate_forest_plot_data()
        
        # Build HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Meta-Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
            color: #1a1a1a;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .header h1 {{
            margin: 0;
            font-size: 36px;
            font-weight: 700;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 16px;
        }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .section-title {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .stat-label {{
            font-size: 13px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: 700;
            color: #667eea;
            margin-top: 8px;
        }}
        .result-box {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #28a745;
        }}
        .result-label {{
            font-weight: 600;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .result-value {{
            font-size: 24px;
            font-weight: 700;
            color: #1a1a1a;
            margin-top: 5px;
        }}
        .study-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .study-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        .study-table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        .study-table tr:hover {{
            background: #f8f9fa;
        }}
        .interpretation {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }}
        .interpretation h3 {{
            margin-top: 0;
            color: #856404;
        }}
        .forest-plot {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .citation-badge {{
            background: #667eea;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .powered-by {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }}
        .powered-by strong {{
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Meta-Analysis Report</h1>
        <p>Generated with Anthropic Citations API - Full Citation Provenance</p>
    </div>
    
    <div class="section">
        <div class="section-title">Overview</div>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Studies Included</div>
                <div class="stat-value">{fixed['n_studies']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Citations</div>
                <div class="stat-value">{sum(len(es.source_citations) for es in self.calculator.effect_sizes)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">I² Statistic</div>
                <div class="stat-value">{random['heterogeneity']['i_squared']:.1f}%</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">Meta-Analysis Results</div>
        
        <h3>Fixed-Effect Model</h3>
        <div class="result-box">
            <div class="result-label">Pooled Odds Ratio</div>
            <div class="result-value">{fixed['pooled_effect']:.3f} (95% CI: {fixed['lower_ci']:.3f} - {fixed['upper_ci']:.3f})</div>
        </div>
        <p>Z = {fixed['z_value']:.3f}, p = {fixed['p_value']:.4f}</p>
        
        <h3>Random-Effects Model (DerSimonian-Laird)</h3>
        <div class="result-box">
            <div class="result-label">Pooled Odds Ratio</div>
            <div class="result-value">{random['pooled_effect']:.3f} (95% CI: {random['lower_ci']:.3f} - {random['upper_ci']:.3f})</div>
        </div>
        <p>Z = {random['z_value']:.3f}, p = {random['p_value']:.4f}</p>
        
        <div class="interpretation">
            <h3>Interpretation</h3>
            <ul>
                <li><strong>Effect:</strong> {
                    "Statistically significant effect detected (p < 0.05)" 
                    if random['p_value'] < 0.05 
                    else "No statistically significant effect (p ≥ 0.05)"
                }</li>
                <li><strong>Heterogeneity:</strong> {
                    "Low" if random['heterogeneity']['i_squared'] < 25 else
                    "Moderate" if random['heterogeneity']['i_squared'] < 50 else
                    "Substantial" if random['heterogeneity']['i_squared'] < 75 else
                    "Considerable"
                } (I² = {random['heterogeneity']['i_squared']:.1f}%)</li>
                <li><strong>Model Selection:</strong> {
                    "Random-effects model recommended due to heterogeneity" 
                    if random['heterogeneity']['i_squared'] > 25 
                    else "Either model appropriate (low heterogeneity)"
                }</li>
            </ul>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">Individual Study Results</div>
        <table class="study-table">
            <thead>
                <tr>
                    <th>Study</th>
                    <th>Odds Ratio</th>
                    <th>95% CI</th>
                    <th>Weight (%)</th>
                    <th>Citations</th>
                </tr>
            </thead>
            <tbody>
"""
        
        total_weight = sum(es.weight for es in self.calculator.effect_sizes)
        for es in self.calculator.effect_sizes:
            or_value = np.exp(es.effect_size)
            weight_pct = (es.weight / total_weight) * 100
            html += f"""
                <tr>
                    <td>{es.study_id}</td>
                    <td>{or_value:.3f}</td>
                    <td>[{es.lower_ci:.3f}, {es.upper_ci:.3f}]</td>
                    <td>{weight_pct:.1f}%</td>
                    <td><span class="citation-badge">{len(es.source_citations)} citations</span></td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <div class="section-title">Heterogeneity Assessment</div>
        <table class="study-table">
            <thead>
                <tr>
                    <th>Statistic</th>
                    <th>Value</th>
                    <th>Interpretation</th>
                </tr>
            </thead>
            <tbody>
"""
        
        het = random['heterogeneity']
        html += f"""
                <tr>
                    <td>Cochran's Q</td>
                    <td>{het['q_statistic']:.2f} (df = {het['df']})</td>
                    <td>p = {het['p_value']:.4f}</td>
                </tr>
                <tr>
                    <td>I² statistic</td>
                    <td>{het['i_squared']:.1f}%</td>
                    <td>{
                        "Low heterogeneity" if het['i_squared'] < 25 else
                        "Moderate heterogeneity" if het['i_squared'] < 50 else
                        "Substantial heterogeneity" if het['i_squared'] < 75 else
                        "Considerable heterogeneity"
                    }</td>
                </tr>
                <tr>
                    <td>τ² (tau-squared)</td>
                    <td>{het['tau_squared']:.4f}</td>
                    <td>Between-study variance</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="powered-by">
        <p>Report generated using <strong>Anthropic Citations API</strong></p>
        <p>All data points tracked with full citation provenance</p>
    </div>
</body>
</html>
"""
        
        return html
    
    def run_complete_workflow(
        self,
        pdf_paths: List[str],
        study_type: str = "clinical_trial",
        output_dir: str = "./meta_analysis_output"
    ):
        """
        Run the complete workflow from PDFs to final report
        """
        print("\n" + "="*70)
        print("COMPLETE META-ANALYSIS WORKFLOW")
        print("="*70)
        print(f"\nInput: {len(pdf_paths)} PDF papers")
        print(f"Study type: {study_type}")
        print(f"Output directory: {output_dir}\n")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            # Step 1: Extract data
            self.step1_extract_data(pdf_paths, study_type, output_dir)
            
            # Step 2: Calculate effect sizes
            self.step2_calculate_effect_sizes(output_dir)
            
            # Step 3: Meta-analysis
            self.step3_meta_analysis(output_dir)
            
            # Step 4: Generate report
            report_path = self.step4_generate_report(output_dir)
            
            print("\n" + "="*70)
            print("✅ WORKFLOW COMPLETE!")
            print("="*70)
            print(f"\nAll outputs saved to: {output_dir}")
            print(f"Final report: {report_path}")
            print("\nFiles generated:")
            print("  - step1_extraction_complete.json (raw extraction with citations)")
            print("  - step1_extraction_data.csv (tabular data)")
            print("  - step1_extraction_citations.json (citation map)")
            print("  - step3_meta_analysis_results.json (statistical results)")
            print("  - FINAL_META_ANALYSIS_REPORT.html (comprehensive report)")
            
            return report_path
            
        except Exception as e:
            print(f"\n❌ Error during workflow: {str(e)}")
            raise


def main():
    """Example usage"""
    
    # Initialize workflow
    workflow = CompleteMetaAnalysisWorkflow()
    
    # Define papers to analyze
    pdf_papers = [
        "/mnt/user-data/uploads/paper1.pdf",
        "/mnt/user-data/uploads/paper2.pdf",
        "/mnt/user-data/uploads/paper3.pdf",
    ]
    
    # Run complete workflow
    try:
        workflow.run_complete_workflow(
            pdf_paths=pdf_papers,
            study_type="surgical",  # or "clinical_trial", "observational"
            output_dir="./cerebellar_meta_analysis"
        )
    except FileNotFoundError:
        print("\n" + "="*70)
        print("EXAMPLE WORKFLOW - No PDFs Found")
        print("="*70)
        print("\nTo use this workflow:")
        print("\n1. Upload your PDF papers to /mnt/user-data/uploads/")
        print("2. Update the pdf_papers list with your file paths")
        print("3. Choose appropriate study_type:")
        print("   - 'clinical_trial' for RCTs")
        print("   - 'surgical' for surgical interventions")
        print("   - 'observational' for cohort/case-control studies")
        print("4. Run this script")
        print("\nThe workflow will:")
        print("  ✓ Extract data from each PDF with citations")
        print("  ✓ Calculate effect sizes (OR, RR, etc.)")
        print("  ✓ Perform meta-analysis (fixed & random effects)")
        print("  ✓ Generate comprehensive HTML report")
        print("  ✓ Track all citations for audit trails")


if __name__ == "__main__":
    import numpy as np  # Required for calculations
    main()
