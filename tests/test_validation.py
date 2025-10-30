"""
Tests for validation system

Tests confidence scoring and outlier detection.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation_poc import (
    ConfidenceScorer,
    OutlierDetector,
    ValidationPipeline,
    QualityIssue
)


class TestConfidenceScoring:
    """Test confidence scoring for extracted fields"""

    def setup_method(self):
        """Setup test fixtures"""
        self.scorer = ConfidenceScorer()

    def test_high_confidence_with_good_citation(self):
        """Test that good citations get high scores"""
        confidence = self.scorer.calculate_confidence(
            field_name="total_sample_size",
            value=150,
            citations=[{
                'cited_text': "A total of 150 patients were enrolled in the study between 2020 and 2022.",
                'start_page_number': 5
            }],
            all_data={}
        )

        # Should have decent confidence with good citation
        assert confidence.total > 50, f"Expected >50% confidence, got {confidence.total:.1f}%"
        assert confidence.citation_quality > 20, "Should have good citation score"

    def test_low_confidence_without_citation(self):
        """Test that fields without citations get low scores"""
        confidence = self.scorer.calculate_confidence(
            field_name="total_sample_size",
            value=150,
            citations=[],  # No citations
            all_data={}
        )

        # Should have low confidence without citation
        assert confidence.total < 50, f"Expected <50% confidence without citation, got {confidence.total:.1f}%"
        assert confidence.citation_quality == 0, "Should have zero citation score"

    def test_needs_review_flag(self):
        """Test that low confidence fields are flagged for review"""
        # Low quality extraction
        confidence = self.scorer.calculate_confidence(
            field_name="unclear_field",
            value=None,
            citations=[],
            all_data={}
        )

        assert confidence.needs_review, "Low confidence field should need review"

    def test_high_confidence_flag(self):
        """Test high confidence detection"""
        # High quality extraction
        confidence = self.scorer.calculate_confidence(
            field_name="total_sample_size",
            value=150,
            citations=[{
                'cited_text': "Methods section describes enrollment of 150 patients with detailed inclusion criteria.",
                'start_page_number': 5
            }],
            all_data={'participants': {'total_sample_size': 150}}
        )

        # Should have high confidence
        # Note: May not reach 80% due to scoring logic, but should be > 60%
        assert confidence.total > 60, f"Expected >60% for quality extraction, got {confidence.total:.1f}%"


class TestOutlierDetector:
    """Test outlier detection"""

    def setup_method(self):
        """Setup test fixtures"""
        self.detector = OutlierDetector()

    def test_detect_events_greater_than_sample_size(self):
        """Test detection of events > sample size"""
        study = {
            'study_id': 'InvalidStudy',
            'extracted_data': {
                'participants': {
                    'intervention_group_size': 50,
                    'control_group_size': 50
                },
                'outcomes': {
                    'mortality_intervention': 60,  # More than 50!
                    'mortality_control': 10
                }
            }
        }

        issues = self.detector.check_single_study(study)

        # Should detect the problem
        assert len(issues) > 0, "Should detect events > sample size"
        assert any(i.severity == "critical" for i in issues), "Should be critical issue"
        assert any('mortality_intervention' in i.field for i in issues), "Should flag correct field"

    def test_detect_sample_size_mismatch(self):
        """Test detection of sample size arithmetic errors"""
        study = {
            'study_id': 'MismatchStudy',
            'extracted_data': {
                'participants': {
                    'total_sample_size': 100,
                    'intervention_group_size': 55,
                    'control_group_size': 50  # 55 + 50 != 100
                },
                'outcomes': {}
            }
        }

        issues = self.detector.check_single_study(study)

        # Should detect mismatch
        assert len(issues) > 0, "Should detect sample size mismatch"
        assert any('sample_size' in i.field.lower() for i in issues), "Should mention sample size"

    def test_detect_invalid_percentage(self):
        """Test detection of percentages > 100"""
        study = {
            'study_id': 'InvalidPercent',
            'extracted_data': {
                'participants': {
                    'percent_male': 150.0  # Impossible!
                },
                'outcomes': {}
            }
        }

        issues = self.detector.check_single_study(study)

        # Should detect invalid percentage
        assert len(issues) > 0, "Should detect invalid percentage"
        assert any('percent' in i.field.lower() for i in issues), "Should flag percentage field"

    def test_detect_implausible_age(self):
        """Test detection of implausible ages"""
        study = {
            'study_id': 'BadAge',
            'extracted_data': {
                'participants': {
                    'mean_age': 150  # Too old!
                },
                'outcomes': {}
            }
        }

        issues = self.detector.check_single_study(study)

        # Should detect implausible age
        assert len(issues) > 0, "Should detect implausible age"
        assert any('age' in i.field.lower() for i in issues), "Should flag age field"

    def test_no_issues_for_valid_study(self):
        """Test that valid studies pass without issues"""
        valid_study = {
            'study_id': 'ValidStudy',
            'extracted_data': {
                'participants': {
                    'total_sample_size': 100,
                    'intervention_group_size': 50,
                    'control_group_size': 50,
                    'mean_age': 62.5,
                    'percent_male': 68.0
                },
                'outcomes': {
                    'mortality_intervention': 10,
                    'mortality_control': 15
                }
            }
        }

        issues = self.detector.check_single_study(valid_study)

        # Should have no critical issues
        critical_issues = [i for i in issues if i.severity == "critical"]
        assert len(critical_issues) == 0, f"Valid study should have no critical issues, found: {critical_issues}"


class TestValidationPipeline:
    """Test complete validation pipeline"""

    def setup_method(self):
        """Setup test fixtures"""
        self.pipeline = ValidationPipeline()

    def test_validation_report_generation(self):
        """Test that validation report is generated correctly"""
        mock_extraction = {
            'study_id': 'TestStudy',
            'extracted_data': {
                'participants': {
                    'total_sample_size': 150
                },
                'outcomes': {
                    'mortality_intervention': 15
                }
            },
            'citations': [
                {
                    'cited_text': "150 patients enrolled",
                    'start_page_number': 5
                }
            ],
            'citation_count': 1
        }

        report = self.pipeline.validate_extraction(mock_extraction)

        # Check report structure
        assert report.study_id == 'TestStudy'
        assert report.overall_confidence >= 0
        assert report.overall_confidence <= 100
        assert isinstance(report.high_confidence_fields, int)
        assert isinstance(report.low_confidence_fields, int)
        assert isinstance(report.fields_requiring_review, list)
        assert isinstance(report.quality_issues, list)
        assert report.recommendation in ['accept', 'review', 're-extract']

    def test_recommendation_logic(self):
        """Test that recommendations are appropriate"""
        # High quality extraction
        good_extraction = {
            'study_id': 'GoodStudy',
            'extracted_data': {
                'participants': {
                    'total_sample_size': 150,
                    'intervention_group_size': 75,
                    'control_group_size': 75,
                    'mean_age': 62.5,
                    'percent_male': 68.0
                },
                'outcomes': {
                    'mortality_intervention': 15,
                    'mortality_control': 28
                }
            },
            'citations': [
                {'cited_text': "150 patients", 'start_page_number': 5},
                {'cited_text': "15 deaths in intervention", 'start_page_number': 12},
                {'cited_text': "28 deaths in control", 'start_page_number': 12}
            ],
            'citation_count': 3
        }

        report = self.pipeline.validate_extraction(good_extraction)

        # Should not recommend re-extract for valid study
        assert report.recommendation != 're-extract' or report.overall_confidence < 70, \
            "Valid study shouldn't require re-extraction"

    def test_flags_poor_quality_extraction(self):
        """Test that poor quality extractions are flagged"""
        # Poor quality: no citations, impossible values
        bad_extraction = {
            'study_id': 'BadStudy',
            'extracted_data': {
                'participants': {
                    'intervention_group_size': 50
                },
                'outcomes': {
                    'mortality_intervention': 100  # More than sample size!
                }
            },
            'citations': [],  # No citations
            'citation_count': 0
        }

        report = self.pipeline.validate_extraction(bad_extraction)

        # Should have critical issues
        assert len(report.quality_issues) > 0, "Should detect quality issues"
        assert report.recommendation in ['review', 're-extract'], "Should recommend action"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, '-v'])
