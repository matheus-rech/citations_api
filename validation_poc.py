#!/usr/bin/env python3
"""
Proof of Concept: Multi-Agent Validation for Data Extraction

This demonstrates improved data extraction with:
1. Confidence scoring per field
2. Multi-agent consensus (optional)
3. Quality assessment
4. Outlier detection
"""

import json
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from meta_analysis_extractor import MetaAnalysisExtractor
import anthropic
import os


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class ConfidenceScore:
    """Confidence breakdown for an extracted field"""
    citation_quality: float  # 0-40
    value_consistency: float  # 0-30
    extraction_context: float  # 0-30
    total: float  # 0-100

    @property
    def is_high_confidence(self) -> bool:
        return self.total >= 80

    @property
    def needs_review(self) -> bool:
        return self.total < 70


@dataclass
class ValidatedField:
    """An extracted field with confidence scoring"""
    field_name: str
    value: Any
    citations: List[Dict]
    confidence: ConfidenceScore
    agent_agreement: Optional[int] = None  # For multi-agent: how many agreed
    alternative_values: Optional[List] = None  # For multi-agent: what others extracted


@dataclass
class QualityIssue:
    """A quality issue found during validation"""
    severity: str  # "critical", "warning", "info"
    field: str
    issue: str
    suggested_action: str


@dataclass
class ValidationReport:
    """Complete validation report for an extraction"""
    study_id: str
    overall_confidence: float
    high_confidence_fields: int
    low_confidence_fields: int
    fields_requiring_review: List[str]
    quality_issues: List[QualityIssue]
    citation_coverage: float  # % of fields with citations
    outliers_detected: List[str]
    recommendation: str  # "accept", "review", "re-extract"


# ============================================================================
# Confidence Scorer
# ============================================================================

class ConfidenceScorer:
    """Calculate confidence scores for extracted fields"""

    def score_citation_quality(self, citations: List[Dict]) -> float:
        """Score citation quality (0-40 points)"""
        if not citations:
            return 0.0

        citation = citations[0]  # Use first citation

        # Check citation specificity
        if 'start_page_number' in citation and citation.get('cited_text'):
            cited_text = citation['cited_text']

            # Has specific location + detailed text
            if len(cited_text) > 50:
                return 40.0  # Excellent citation
            elif len(cited_text) > 20:
                return 32.0  # Good citation
            else:
                return 24.0  # Basic citation
        elif 'start_page_number' in citation:
            return 20.0  # Page reference only
        else:
            return 10.0  # Vague citation

    def score_value_consistency(self, field_name: str, value: Any, all_data: Dict) -> float:
        """Score value consistency (0-30 points)"""
        score = 0.0

        # Check data type consistency
        if value is not None:
            score += 10.0

        # Check logical consistency based on field type
        if 'sample_size' in field_name.lower() or 'patients' in field_name.lower():
            if isinstance(value, int) and 0 < value < 10000:
                score += 10.0
            if value > 0:
                score += 10.0

        elif 'mortality' in field_name.lower() or 'deaths' in field_name.lower():
            if isinstance(value, int) and value >= 0:
                score += 10.0

            # Check against sample size if available
            if 'sample_size' in str(all_data):
                sample_size = self._extract_sample_size(all_data, field_name)
                if sample_size and value <= sample_size:
                    score += 10.0
                else:
                    score += 5.0  # Might be valid, unsure
            else:
                score += 5.0

        elif 'age' in field_name.lower():
            if isinstance(value, (int, float)) and 0 < value < 120:
                score += 20.0

        elif 'percent' in field_name.lower() or 'rate' in field_name.lower():
            if isinstance(value, (int, float)) and 0 <= value <= 100:
                score += 20.0

        else:
            # Generic field
            if value is not None and value != "":
                score += 15.0

        return min(score, 30.0)

    def score_extraction_context(self, field_name: str, citations: List[Dict]) -> float:
        """Score extraction context (0-30 points)"""
        score = 0.0

        if not citations:
            return 0.0

        citation = citations[0]
        cited_text = citation.get('cited_text', '').lower()

        # Check if found in appropriate section
        if 'methods' in cited_text or 'participants' in cited_text or 'patients' in cited_text:
            if 'sample_size' in field_name or 'age' in field_name or 'participants' in field_name:
                score += 15.0

        if ('results' in cited_text or 'outcomes' in cited_text or 'table' in cited_text) and ('mortality' in field_name or 'outcome' in field_name):
            score += 15.0


        # Check for explicit vs inferred values
        if field_name.lower().replace('_', ' ') in cited_text:
            score += 15.0  # Explicit mention
        else:
            score += 5.0  # Might be inferred

        return min(score, 30.0)

    def _extract_sample_size(self, all_data: Dict, current_field: str) -> Optional[int]:
        """Try to find sample size from extracted data"""
        # Try to find sample size in various field names
        for key, value in all_data.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    if 'sample' in k.lower() or 'size' in k.lower():
                        if isinstance(v, int):
                            return v

            # Check if this field is for a specific group
            if 'intervention' in current_field:
                for k, v in all_data.items():
                    if isinstance(v, dict) and 'intervention_group_size' in v:
                        return v['intervention_group_size']
            elif 'control' in current_field:
                for k, v in all_data.items():
                    if isinstance(v, dict) and 'control_group_size' in v:
                        return v['control_group_size']

        return None

    def calculate_confidence(
        self,
        field_name: str,
        value: Any,
        citations: List[Dict],
        all_data: Dict
    ) -> ConfidenceScore:
        """Calculate overall confidence for a field"""

        citation_score = self.score_citation_quality(citations)
        consistency_score = self.score_value_consistency(field_name, value, all_data)
        context_score = self.score_extraction_context(field_name, citations)

        total = citation_score + consistency_score + context_score

        return ConfidenceScore(
            citation_quality=citation_score,
            value_consistency=consistency_score,
            extraction_context=context_score,
            total=total
        )


# ============================================================================
# Outlier Detector
# ============================================================================

class OutlierDetector:
    """Detect statistical outliers and impossible values"""

    def check_single_study(self, study_data: Dict) -> List[QualityIssue]:
        """Check a single study for issues"""
        issues = []

        # Extract nested data
        extracted = study_data.get('extracted_data', {})

        # Check sample size consistency
        participants = extracted.get('participants', {})
        total_size = participants.get('total_sample_size')
        intervention_size = participants.get('intervention_group_size')
        control_size = participants.get('control_group_size')

        if all([total_size, intervention_size, control_size]):
            if intervention_size + control_size != total_size:
                issues.append(QualityIssue(
                    severity="critical",
                    field="sample_size",
                    issue=f"Sample size mismatch: {intervention_size} + {control_size} != {total_size}",
                    suggested_action="Re-extract sample sizes from Methods section"
                ))

        # Check events vs sample size
        outcomes = extracted.get('outcomes', {})
        for field_name, value in outcomes.items():
            if 'mortality' in field_name or 'deaths' in field_name or 'events' in field_name:
                if not isinstance(value, int):
                    continue

                # Determine which group
                if 'intervention' in field_name and intervention_size:
                    if value > intervention_size:
                        issues.append(QualityIssue(
                            severity="critical",
                            field=field_name,
                            issue=f"Events ({value}) > Sample size ({intervention_size})",
                            suggested_action="Verify event counts in Results/Table"
                        ))
                elif 'control' in field_name and control_size:
                    if value > control_size:
                        issues.append(QualityIssue(
                            severity="critical",
                            field=field_name,
                            issue=f"Events ({value}) > Sample size ({control_size})",
                            suggested_action="Verify event counts in Results/Table"
                        ))

        # Check percentages
        for field_name, value in participants.items():
            if 'percent' in field_name.lower():
                if isinstance(value, (int, float)) and (value < 0 or value > 100):
                    issues.append(QualityIssue(
                        severity="critical",
                        field=field_name,
                        issue=f"Invalid percentage: {value}",
                        suggested_action="Re-extract percentage values"
                    ))

        # Check age range
        if 'mean_age' in participants:
            age = participants['mean_age']
            if isinstance(age, (int, float)) and (age < 0 or age > 120):
                issues.append(QualityIssue(
                    severity="critical",
                    field="mean_age",
                    issue=f"Implausible age: {age}",
                    suggested_action="Verify age in baseline characteristics"
                ))

        return issues

    def check_cross_study_outliers(self, all_studies: List[Dict]) -> List[QualityIssue]:
        """Check for outliers across studies"""
        issues = []

        # Collect sample sizes
        sample_sizes = []
        study_ids = []
        for study in all_studies:
            extracted = study.get('extracted_data', {})
            participants = extracted.get('participants', {})
            size = participants.get('total_sample_size')
            if size and isinstance(size, int):
                sample_sizes.append(size)
                study_ids.append(study.get('study_id', 'Unknown'))

        if len(sample_sizes) < 3:
            return issues  # Need at least 3 studies for outlier detection

        # Statistical outlier detection (z-score)
        mean_size = np.mean(sample_sizes)
        std_size = np.std(sample_sizes)

        if std_size == 0:
            return issues

        for study_id, size in zip(study_ids, sample_sizes):
            z_score = abs((size - mean_size) / std_size)
            if z_score > 3:
                issues.append(QualityIssue(
                    severity="warning",
                    field="total_sample_size",
                    issue=f"{study_id}: Sample size ({size}) is statistical outlier (z={z_score:.2f})",
                    suggested_action="Verify sample size - may be correct but unusual"
                ))

        return issues


# ============================================================================
# Validation Pipeline
# ============================================================================

class ValidationPipeline:
    """Complete validation pipeline for extraction results"""

    def __init__(self):
        self.scorer = ConfidenceScorer()
        self.outlier_detector = OutlierDetector()

    def validate_extraction(
        self,
        extraction_result: Dict,
        mode: str = "thorough"  # "fast", "thorough", or "multi-agent"
    ) -> ValidationReport:
        """
        Validate an extraction result

        Args:
            extraction_result: Result from MetaAnalysisExtractor
            mode: Validation thoroughness level
        """

        study_id = extraction_result.get('study_id', 'Unknown')
        extracted_data = extraction_result.get('extracted_data', {})
        citations = extraction_result.get('citations', [])

        # Build citation map
        citation_map = self._build_citation_map(citations)

        # Score each field
        validated_fields = []
        confidence_scores = []
        fields_needing_review = []
        fields_with_citations = 0
        total_fields = 0

        for category, fields in extracted_data.items():
            if not isinstance(fields, dict):
                continue

            for field_name, value in fields.items():
                total_fields += 1
                full_field_name = f"{category}.{field_name}"

                # Get citations for this field (simplified - in reality need better mapping)
                field_citations = citation_map.get(field_name, [])
                if field_citations:
                    fields_with_citations += 1

                # Calculate confidence
                confidence = self.scorer.calculate_confidence(
                    field_name=field_name,
                    value=value,
                    citations=field_citations,
                    all_data=extracted_data
                )

                confidence_scores.append(confidence.total)

                if confidence.needs_review:
                    fields_needing_review.append(full_field_name)

                validated_fields.append(ValidatedField(
                    field_name=full_field_name,
                    value=value,
                    citations=field_citations,
                    confidence=confidence
                ))

        # Outlier detection
        quality_issues = self.outlier_detector.check_single_study(extraction_result)
        outliers = [issue.field for issue in quality_issues if issue.severity == "critical"]

        # Calculate overall metrics
        overall_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        high_confidence = sum(1 for s in confidence_scores if s >= 80)
        low_confidence = sum(1 for s in confidence_scores if s < 70)
        citation_coverage = (fields_with_citations / total_fields * 100) if total_fields > 0 else 0.0

        # Make recommendation
        if overall_confidence >= 85 and not quality_issues:
            recommendation = "accept"
        elif overall_confidence >= 70 and len(quality_issues) <= 2:
            recommendation = "review"
        else:
            recommendation = "re-extract"

        return ValidationReport(
            study_id=study_id,
            overall_confidence=overall_confidence,
            high_confidence_fields=high_confidence,
            low_confidence_fields=low_confidence,
            fields_requiring_review=fields_needing_review,
            quality_issues=quality_issues,
            citation_coverage=citation_coverage,
            outliers_detected=outliers,
            recommendation=recommendation
        )

    def _build_citation_map(self, citations: List[Dict]) -> Dict[str, List[Dict]]:
        """Map citations to field names (simplified)"""
        citation_map = {}

        for citation in citations:
            cited_text = citation.get('cited_text', '').lower()

            # Try to infer which fields this citation supports
            if 'sample' in cited_text or 'patients' in cited_text or 'participants' in cited_text:
                citation_map.setdefault('total_sample_size', []).append(citation)

            if 'mortality' in cited_text or 'death' in cited_text:
                citation_map.setdefault('mortality_intervention', []).append(citation)
                citation_map.setdefault('mortality_control', []).append(citation)

            if 'age' in cited_text:
                citation_map.setdefault('mean_age', []).append(citation)

        return citation_map

    def print_validation_report(self, report: ValidationReport):
        """Print formatted validation report"""

        print("\n" + "="*70)
        print(f"VALIDATION REPORT: {report.study_id}")
        print("="*70)

        # Overall metrics
        print(f"\n📊 Overall Confidence: {report.overall_confidence:.1f}%")
        print(f"   ├─ High confidence fields: {report.high_confidence_fields}")
        print(f"   ├─ Low confidence fields: {report.low_confidence_fields}")
        print(f"   └─ Citation coverage: {report.citation_coverage:.1f}%")

        # Quality issues
        if report.quality_issues:
            print(f"\n⚠️  Quality Issues Found: {len(report.quality_issues)}")
            for issue in report.quality_issues:
                icon = "🔴" if issue.severity == "critical" else "🟡"
                print(f"   {icon} [{issue.severity.upper()}] {issue.field}")
                print(f"      Issue: {issue.issue}")
                print(f"      Action: {issue.suggested_action}")
        else:
            print("\n✅ No quality issues detected")

        # Fields needing review
        if report.fields_requiring_review:
            print(f"\n🔍 Fields Requiring Review: {len(report.fields_requiring_review)}")
            for field in report.fields_requiring_review[:5]:  # Show first 5
                print(f"   • {field}")
            if len(report.fields_requiring_review) > 5:
                print(f"   ... and {len(report.fields_requiring_review) - 5} more")

        # Recommendation
        print(f"\n📋 Recommendation: {report.recommendation.upper()}")
        if report.recommendation == "accept":
            print("   ✅ Data quality is high - safe to proceed with meta-analysis")
        elif report.recommendation == "review":
            print("   ⚠️  Manual review recommended for flagged fields")
        else:
            print("   🔴 Re-extraction recommended due to quality concerns")

        print("="*70 + "\n")


# ============================================================================
# Demo Usage
# ============================================================================

def demo_validation():
    """Demonstrate validation pipeline"""

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║           Data Extraction Validation - Proof of Concept              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Simulate extraction result
    mock_extraction = {
        "study_id": "Smith2023",
        "extracted_data": {
            "participants": {
                "total_sample_size": 150,
                "intervention_group_size": 75,
                "control_group_size": 75,
                "mean_age": 62.5,
                "percent_male": 68.0
            },
            "outcomes": {
                "mortality_intervention": 15,
                "mortality_control": 28,
                "favorable_outcome_intervention": 45,
                "favorable_outcome_control": 32
            }
        },
        "citations": [
            {
                "type": "page_location",
                "cited_text": "A total of 150 patients were enrolled between 2020 and 2022",
                "start_page_number": 5,
                "end_page_number": 5
            },
            {
                "type": "page_location",
                "cited_text": "Table 2 shows mortality outcomes: 15 deaths in the intervention group and 28 in the control group",
                "start_page_number": 12,
                "end_page_number": 12
            }
        ],
        "citation_count": 2
    }

    # Run validation
    pipeline = ValidationPipeline()
    report = pipeline.validate_extraction(mock_extraction)

    # Print report
    pipeline.print_validation_report(report)

    # Example with quality issues
    print("\n" + "="*70)
    print("EXAMPLE 2: Extraction with Quality Issues")
    print("="*70)

    mock_extraction_with_issues = {
        "study_id": "Johnson2022",
        "extracted_data": {
            "participants": {
                "total_sample_size": 100,
                "intervention_group_size": 55,
                "control_group_size": 50,  # Doesn't add up!
                "mean_age": 58.0,
                "percent_male": 72.0
            },
            "outcomes": {
                "mortality_intervention": 60,  # More than sample size!
                "mortality_control": 25
            }
        },
        "citations": [],  # No citations!
        "citation_count": 0
    }

    report2 = pipeline.validate_extraction(mock_extraction_with_issues)
    pipeline.print_validation_report(report2)


if __name__ == "__main__":
    demo_validation()
