"""
Unit tests for MetaAnalysisCalculator

Critical tests for statistical functions - these MUST pass before production deployment.
"""

import pytest
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meta_analysis_calculator import MetaAnalysisCalculator


class TestOddsRatioCalculation:
    """Test odds ratio calculations"""

    def setup_method(self):
        """Setup test fixtures"""
        self.calculator = MetaAnalysisCalculator([])

    def test_basic_odds_ratio(self):
        """Test OR calculation with known values"""
        # Test case: 2x2 table
        # Intervention: 10 events / 50 patients
        # Control: 20 events / 50 patients
        # Expected OR = (10/40) / (20/30) = 0.375

        log_or, se, ci_lower, ci_upper = self.calculator.calculate_odds_ratio(
            events_treatment=10,
            n_treatment=50,
            events_control=20,
            n_control=50
        )

        or_value = np.exp(log_or)

        # Check OR is approximately correct
        assert abs(or_value - 0.375) < 0.01, f"Expected OR ~0.375, got {or_value:.3f}"

        # Check confidence interval
        assert ci_lower < or_value < ci_upper, "OR should be within confidence interval"

        # Check standard error is positive
        assert se > 0, "Standard error should be positive"

    def test_odds_ratio_no_effect(self):
        """Test OR when no difference between groups"""
        # Equal event rates: 10/50 in both groups
        # Expected OR = 1.0

        log_or, se, ci_lower, ci_upper = self.calculator.calculate_odds_ratio(
            events_treatment=10,
            n_treatment=50,
            events_control=10,
            n_control=50
        )

        or_value = np.exp(log_or)

        assert abs(or_value - 1.0) < 0.01, f"Expected OR ~1.0 for no effect, got {or_value:.3f}"

        # CI should include 1.0
        assert ci_lower < 1.0 < ci_upper, "CI should include 1.0 for no effect"

    def test_odds_ratio_zero_cell_correction(self):
        """Test continuity correction when events = 0"""
        # Zero events in treatment group
        log_or, se, ci_lower, ci_upper = self.calculator.calculate_odds_ratio(
            events_treatment=0,
            n_treatment=50,
            events_control=10,
            n_control=50
        )

        # Should return valid values (with 0.5 correction applied)
        assert log_or is not None, "Should handle zero cells"
        assert not np.isinf(log_or), "log(OR) should not be infinite"
        assert not np.isinf(ci_lower), "CI lower should not be infinite"
        assert not np.isinf(ci_upper), "CI upper should not be infinite"
        assert se > 0, "SE should be positive"

    def test_odds_ratio_invalid_inputs(self):
        """Test that invalid inputs are rejected"""
        # Events > sample size should raise error
        with pytest.raises((ValueError, AssertionError)):
            self.calculator.calculate_odds_ratio(
                events_treatment=60,  # More than n_treatment!
                n_treatment=50,
                events_control=10,
                n_control=50
            )

    def test_odds_ratio_negative_values(self):
        """Test that negative values are rejected"""
        with pytest.raises((ValueError, AssertionError)):
            self.calculator.calculate_odds_ratio(
                events_treatment=-5,  # Negative!
                n_treatment=50,
                events_control=10,
                n_control=50
            )


class TestRiskRatioCalculation:
    """Test risk ratio calculations"""

    def setup_method(self):
        """Setup test fixtures"""
        self.calculator = MetaAnalysisCalculator([])

    def test_basic_risk_ratio(self):
        """Test RR calculation with known values"""
        # Risk in treatment: 10/50 = 0.20
        # Risk in control: 20/50 = 0.40
        # Expected RR = 0.20 / 0.40 = 0.50

        log_rr, se, ci_lower, ci_upper = self.calculator.calculate_risk_ratio(
            events_treatment=10,
            n_treatment=50,
            events_control=20,
            n_control=50
        )

        rr_value = np.exp(log_rr)

        assert abs(rr_value - 0.50) < 0.01, f"Expected RR ~0.50, got {rr_value:.3f}"
        assert ci_lower < rr_value < ci_upper, "RR should be within CI"

    def test_risk_ratio_no_effect(self):
        """Test RR when no difference"""
        log_rr, se, ci_lower, ci_upper = self.calculator.calculate_risk_ratio(
            events_treatment=10,
            n_treatment=50,
            events_control=10,
            n_control=50
        )

        rr_value = np.exp(log_rr)

        assert abs(rr_value - 1.0) < 0.01, f"Expected RR ~1.0, got {rr_value:.3f}"
        assert ci_lower < 1.0 < ci_upper, "CI should include 1.0"


class TestStandardizedMeanDifference:
    """Test SMD (Hedges' g) calculations"""

    def setup_method(self):
        """Setup test fixtures"""
        self.calculator = MetaAnalysisCalculator([])

    def test_basic_smd(self):
        """Test SMD with known values"""
        # Treatment: mean=5.0, sd=2.0, n=50
        # Control: mean=3.0, sd=2.0, n=50
        # Expected SMD (Cohen's d) ≈ (5-3)/2 = 1.0
        # Hedges' g is bias-corrected, slightly less than 1.0

        smd, se, ci_lower, ci_upper = self.calculator.calculate_standardized_mean_difference(
            mean_treatment=5.0,
            sd_treatment=2.0,
            n_treatment=50,
            mean_control=3.0,
            sd_control=2.0,
            n_control=50
        )

        # Hedges' g should be close to 1.0 but slightly smaller
        assert 0.95 < smd < 1.05, f"Expected SMD ~1.0, got {smd:.3f}"
        assert ci_lower < smd < ci_upper, "SMD should be within CI"
        assert se > 0, "SE should be positive"

    def test_smd_no_effect(self):
        """Test SMD when means are equal"""
        smd, se, ci_lower, ci_upper = self.calculator.calculate_standardized_mean_difference(
            mean_treatment=5.0,
            sd_treatment=2.0,
            n_treatment=50,
            mean_control=5.0,  # Same mean
            sd_control=2.0,
            n_control=50
        )

        assert abs(smd) < 0.01, f"Expected SMD ~0.0, got {smd:.3f}"
        assert ci_lower < 0.0 < ci_upper, "CI should include 0.0"

    def test_smd_negative_effect(self):
        """Test SMD when control > treatment"""
        smd, se, ci_lower, ci_upper = self.calculator.calculate_standardized_mean_difference(
            mean_treatment=3.0,
            sd_treatment=2.0,
            n_treatment=50,
            mean_control=5.0,  # Control higher
            sd_control=2.0,
            n_control=50
        )

        assert smd < 0, f"Expected negative SMD, got {smd:.3f}"


class TestMetaAnalysis:
    """Test meta-analysis pooling"""

    def setup_method(self):
        """Setup with mock extraction results"""
        # Create mock extraction results for 3 studies
        self.mock_results = [
            {
                'study_id': 'Study1',
                'extracted_data': {
                    'outcomes': {
                        'mortality_intervention': 10,
                        'mortality_control': 20
                    },
                    'participants': {
                        'intervention_group_size': 50,
                        'control_group_size': 50
                    }
                }
            },
            {
                'study_id': 'Study2',
                'extracted_data': {
                    'outcomes': {
                        'mortality_intervention': 15,
                        'mortality_control': 25
                    },
                    'participants': {
                        'intervention_group_size': 60,
                        'control_group_size': 60
                    }
                }
            },
            {
                'study_id': 'Study3',
                'extracted_data': {
                    'outcomes': {
                        'mortality_intervention': 8,
                        'mortality_control': 18
                    },
                    'participants': {
                        'intervention_group_size': 40,
                        'control_group_size': 40
                    }
                }
            }
        ]

        self.calculator = MetaAnalysisCalculator(self.mock_results)
        self.calculator.extract_dichotomous_outcomes()

    def test_fixed_effect_meta_analysis(self):
        """Test fixed-effect meta-analysis"""
        results = self.calculator.perform_fixed_effect_meta_analysis()

        # Check required fields exist
        assert 'pooled_effect' in results
        assert 'standard_error' in results
        assert 'lower_ci' in results
        assert 'upper_ci' in results
        assert 'z_score' in results
        assert 'p_value' in results

        # Check values are reasonable
        assert results['pooled_effect'] is not None
        assert results['standard_error'] > 0
        assert results['lower_ci'] < results['upper_ci']
        assert 0 <= results['p_value'] <= 1

    def test_random_effects_meta_analysis(self):
        """Test random-effects meta-analysis"""
        results = self.calculator.perform_random_effects_meta_analysis()

        # Check required fields
        assert 'pooled_effect' in results
        assert 'heterogeneity' in results

        # Check heterogeneity metrics
        het = results['heterogeneity']
        assert 'q_statistic' in het
        assert 'i_squared' in het
        assert 'tau_squared' in het

        # I² should be between 0 and 100
        assert 0 <= het['i_squared'] <= 100

        # Tau² should be non-negative
        assert het['tau_squared'] >= 0

    def test_meta_analysis_with_single_study(self):
        """Test meta-analysis handles single study"""
        single_study = [self.mock_results[0]]
        calculator = MetaAnalysisCalculator(single_study)
        calculator.extract_dichotomous_outcomes()

        results = calculator.perform_fixed_effect_meta_analysis()

        # Should still return valid results
        assert results is not None
        assert 'pooled_effect' in results


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, '-v'])
