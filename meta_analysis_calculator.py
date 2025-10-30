"""
Meta-Analysis Calculator
Performs statistical meta-analysis on extracted data with citation provenance
"""

import json
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')


@dataclass
class EffectSize:
    """Store effect size calculation with source citations"""
    study_id: str
    effect_size: float
    standard_error: float
    variance: float
    weight: float
    lower_ci: float
    upper_ci: float
    source_citations: List[Dict[str, Any]]


class MetaAnalysisCalculator:
    """Calculate meta-analysis statistics from extracted data"""
    
    def __init__(self, results: List[Dict[str, Any]]):
        """
        Initialize with extraction results from Citations API
        
        Args:
            results: List of extraction results with citations
        """
        self.results = results
        self.effect_sizes = []
    
    def calculate_odds_ratio(
        self,
        events_treatment: int,
        n_treatment: int,
        events_control: int,
        n_control: int
    ) -> Tuple[float, float, float, float]:
        """
        Calculate odds ratio and confidence interval
        
        Returns:
            (log_or, se_log_or, lower_ci, upper_ci)
        """
        # Add 0.5 to cells with zero (continuity correction)
        if events_treatment == 0 or events_control == 0 or \
           (n_treatment - events_treatment) == 0 or (n_control - events_control) == 0:
            events_treatment += 0.5
            events_control += 0.5
            n_treatment += 1
            n_control += 1
        
        # Calculate odds ratio
        or_value = (events_treatment / (n_treatment - events_treatment)) / \
                   (events_control / (n_control - events_control))
        
        # Log odds ratio
        log_or = np.log(or_value)
        
        # Standard error of log odds ratio
        se_log_or = np.sqrt(
            1/events_treatment + 1/(n_treatment - events_treatment) +
            1/events_control + 1/(n_control - events_control)
        )
        
        # 95% CI
        z = 1.96
        lower_ci = np.exp(log_or - z * se_log_or)
        upper_ci = np.exp(log_or + z * se_log_or)
        
        return log_or, se_log_or, lower_ci, upper_ci
    
    def calculate_risk_ratio(
        self,
        events_treatment: int,
        n_treatment: int,
        events_control: int,
        n_control: int
    ) -> Tuple[float, float, float, float]:
        """
        Calculate risk ratio (relative risk) and confidence interval
        
        Returns:
            (log_rr, se_log_rr, lower_ci, upper_ci)
        """
        # Add 0.5 to cells with zero
        if events_treatment == 0 or events_control == 0:
            events_treatment += 0.5
            events_control += 0.5
            n_treatment += 1
            n_control += 1
        
        # Calculate risk ratio
        risk_treatment = events_treatment / n_treatment
        risk_control = events_control / n_control
        rr = risk_treatment / risk_control
        
        # Log risk ratio
        log_rr = np.log(rr)
        
        # Standard error of log risk ratio
        se_log_rr = np.sqrt(
            (1/events_treatment - 1/n_treatment) +
            (1/events_control - 1/n_control)
        )
        
        # 95% CI
        z = 1.96
        lower_ci = np.exp(log_rr - z * se_log_rr)
        upper_ci = np.exp(log_rr + z * se_log_rr)
        
        return log_rr, se_log_rr, lower_ci, upper_ci
    
    def calculate_standardized_mean_difference(
        self,
        mean_treatment: float,
        sd_treatment: float,
        n_treatment: int,
        mean_control: float,
        sd_control: float,
        n_control: int
    ) -> Tuple[float, float, float, float]:
        """
        Calculate Hedges' g (corrected standardized mean difference)
        
        Returns:
            (hedges_g, se, lower_ci, upper_ci)
        """
        # Pooled standard deviation
        pooled_sd = np.sqrt(
            ((n_treatment - 1) * sd_treatment**2 + 
             (n_control - 1) * sd_control**2) /
            (n_treatment + n_control - 2)
        )
        
        # Cohen's d
        cohens_d = (mean_treatment - mean_control) / pooled_sd
        
        # Correction factor (Hedges' g)
        n_total = n_treatment + n_control
        j = 1 - (3 / (4 * n_total - 9))
        hedges_g = cohens_d * j
        
        # Standard error
        se = np.sqrt(
            (n_treatment + n_control) / (n_treatment * n_control) +
            hedges_g**2 / (2 * (n_treatment + n_control))
        )
        
        # 95% CI
        z = 1.96
        lower_ci = hedges_g - z * se
        upper_ci = hedges_g + z * se
        
        return hedges_g, se, lower_ci, upper_ci
    
    def extract_dichotomous_outcomes(
        self,
        outcome_field: str = "outcomes"
    ) -> List[EffectSize]:
        """
        Extract dichotomous outcomes (e.g., mortality, favorable outcome)
        and calculate effect sizes
        """
        effect_sizes = []
        
        for result in self.results:
            if "error" in result:
                continue
            
            extracted = result.get("extracted_data", {})
            outcomes = extracted.get(outcome_field, {})
            participants = extracted.get("participants", {})
            
            # Get sample sizes
            n_treatment = participants.get("intervention_group_size") or \
                         participants.get("sdc_group_size") or \
                         participants.get("total_sample_size", 0) // 2
            
            n_control = participants.get("control_group_size") or \
                       participants.get("conservative_group_size") or \
                       participants.get("total_sample_size", 0) // 2
            
            # Get events (e.g., deaths, favorable outcomes)
            events_treatment = outcomes.get("mortality_intervention") or \
                             outcomes.get("mortality_sdc")
            
            events_control = outcomes.get("mortality_control") or \
                           outcomes.get("mortality_conservative")
            
            if all(v is not None for v in [events_treatment, events_control, 
                                           n_treatment, n_control]):
                # Calculate odds ratio
                log_or, se, lower_ci, upper_ci = self.calculate_odds_ratio(
                    events_treatment, n_treatment,
                    events_control, n_control
                )
                
                effect_size = EffectSize(
                    study_id=result.get("document_title", "Unknown"),
                    effect_size=log_or,
                    standard_error=se,
                    variance=se**2,
                    weight=1 / (se**2),
                    lower_ci=lower_ci,
                    upper_ci=upper_ci,
                    source_citations=result.get("citations", [])
                )
                
                effect_sizes.append(effect_size)
        
        self.effect_sizes = effect_sizes
        return effect_sizes
    
    def perform_fixed_effect_meta_analysis(self) -> Dict[str, Any]:
        """
        Perform fixed-effect meta-analysis using inverse variance weighting
        """
        if not self.effect_sizes:
            raise ValueError("No effect sizes calculated. Run extract_* method first.")
        
        # Calculate weights
        weights = np.array([es.weight for es in self.effect_sizes])
        effects = np.array([es.effect_size for es in self.effect_sizes])
        
        # Pooled effect size
        pooled_effect = np.sum(weights * effects) / np.sum(weights)
        
        # Standard error of pooled effect
        pooled_se = np.sqrt(1 / np.sum(weights))
        
        # 95% CI
        z = 1.96
        pooled_lower_ci = pooled_effect - z * pooled_se
        pooled_upper_ci = pooled_effect + z * pooled_se
        
        # Z-test and p-value
        z_value = pooled_effect / pooled_se
        p_value = 2 * (1 - self._normal_cdf(abs(z_value)))
        
        # Heterogeneity statistics (Cochran's Q)
        q_statistic = np.sum(weights * (effects - pooled_effect)**2)
        df = len(self.effect_sizes) - 1
        p_heterogeneity = 1 - self._chi_square_cdf(q_statistic, df)
        
        # I² statistic
        i_squared = max(0, ((q_statistic - df) / q_statistic) * 100)
        
        return {
            "method": "Fixed-effect (Inverse Variance)",
            "pooled_log_effect": pooled_effect,
            "pooled_effect": np.exp(pooled_effect),
            "standard_error": pooled_se,
            "lower_ci": np.exp(pooled_lower_ci),
            "upper_ci": np.exp(pooled_upper_ci),
            "z_value": z_value,
            "p_value": p_value,
            "n_studies": len(self.effect_sizes),
            "heterogeneity": {
                "q_statistic": q_statistic,
                "df": df,
                "p_value": p_heterogeneity,
                "i_squared": i_squared,
                "tau_squared": 0  # Fixed effect model assumes tau² = 0
            }
        }
    
    def perform_random_effects_meta_analysis(self) -> Dict[str, Any]:
        """
        Perform random-effects meta-analysis using DerSimonian-Laird method
        """
        if not self.effect_sizes:
            raise ValueError("No effect sizes calculated. Run extract_* method first.")
        
        # Calculate weights
        weights = np.array([es.weight for es in self.effect_sizes])
        effects = np.array([es.effect_size for es in self.effect_sizes])
        
        # Fixed-effect pooled estimate
        pooled_fe = np.sum(weights * effects) / np.sum(weights)
        
        # Cochran's Q
        q_statistic = np.sum(weights * (effects - pooled_fe)**2)
        df = len(self.effect_sizes) - 1
        
        # Tau² (between-study variance) using DerSimonian-Laird
        c = np.sum(weights) - np.sum(weights**2) / np.sum(weights)
        tau_squared = max(0, (q_statistic - df) / c)
        
        # Random-effects weights
        re_weights = 1 / (1/weights + tau_squared)
        
        # Pooled effect size
        pooled_effect = np.sum(re_weights * effects) / np.sum(re_weights)
        
        # Standard error
        pooled_se = np.sqrt(1 / np.sum(re_weights))
        
        # 95% CI
        z = 1.96
        pooled_lower_ci = pooled_effect - z * pooled_se
        pooled_upper_ci = pooled_effect + z * pooled_se
        
        # Z-test and p-value
        z_value = pooled_effect / pooled_se
        p_value = 2 * (1 - self._normal_cdf(abs(z_value)))
        
        # Heterogeneity
        p_heterogeneity = 1 - self._chi_square_cdf(q_statistic, df)
        i_squared = max(0, ((q_statistic - df) / q_statistic) * 100)
        
        return {
            "method": "Random-effects (DerSimonian-Laird)",
            "pooled_log_effect": pooled_effect,
            "pooled_effect": np.exp(pooled_effect),
            "standard_error": pooled_se,
            "lower_ci": np.exp(pooled_lower_ci),
            "upper_ci": np.exp(pooled_upper_ci),
            "z_value": z_value,
            "p_value": p_value,
            "n_studies": len(self.effect_sizes),
            "heterogeneity": {
                "q_statistic": q_statistic,
                "df": df,
                "p_value": p_heterogeneity,
                "i_squared": i_squared,
                "tau_squared": tau_squared
            }
        }
    
    def generate_forest_plot_data(self) -> pd.DataFrame:
        """
        Generate data for forest plot visualization
        """
        if not self.effect_sizes:
            raise ValueError("No effect sizes calculated.")
        
        data = []
        for es in self.effect_sizes:
            data.append({
                "study": es.study_id,
                "effect_size": np.exp(es.effect_size),  # Convert log OR to OR
                "lower_ci": es.lower_ci,
                "upper_ci": es.upper_ci,
                "weight": es.weight,
                "citation_count": len(es.source_citations)
            })
        
        return pd.DataFrame(data)
    
    def create_citation_map(self) -> Dict[str, List[Dict]]:
        """
        Create a map of which citations support which data points
        """
        citation_map = {}
        
        for es in self.effect_sizes:
            citation_map[es.study_id] = {
                "effect_size": es.effect_size,
                "citations": es.source_citations,
                "citation_summary": [
                    {
                        "text": c.get("cited_text", "")[:100],
                        "location": f"Page {c.get('start_page_number', '?')}"
                        if c.get("type") == "page_location"
                        else f"Char {c.get('start_char_index', '?')}"
                    }
                    for c in es.source_citations
                ]
            }
        
        return citation_map
    
    def export_results(
        self,
        fixed_results: Dict[str, Any],
        random_results: Dict[str, Any],
        output_path: str = "meta_analysis_results.json"
    ):
        """Export complete meta-analysis results with citations"""
        
        results = {
            "fixed_effect_model": fixed_results,
            "random_effects_model": random_results,
            "individual_studies": [
                {
                    "study_id": es.study_id,
                    "odds_ratio": np.exp(es.effect_size),
                    "log_odds_ratio": es.effect_size,
                    "standard_error": es.standard_error,
                    "lower_ci": es.lower_ci,
                    "upper_ci": es.upper_ci,
                    "weight": es.weight,
                    "citation_count": len(es.source_citations)
                }
                for es in self.effect_sizes
            ],
            "citation_provenance": self.create_citation_map(),
            "forest_plot_data": self.generate_forest_plot_data().to_dict('records')
        }
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Results exported to: {output_path}")
        
        return results
    
    def print_summary(
        self,
        fixed_results: Dict[str, Any],
        random_results: Dict[str, Any]
    ):
        """Print human-readable summary"""
        
        print("\n" + "="*70)
        print("META-ANALYSIS RESULTS")
        print("="*70)
        
        print(f"\nNumber of studies included: {fixed_results['n_studies']}")
        print(f"Total citations tracked: {sum(len(es.source_citations) for es in self.effect_sizes)}")
        
        print("\n--- FIXED-EFFECT MODEL ---")
        print(f"Pooled Odds Ratio: {fixed_results['pooled_effect']:.3f}")
        print(f"95% CI: [{fixed_results['lower_ci']:.3f}, {fixed_results['upper_ci']:.3f}]")
        print(f"Z = {fixed_results['z_value']:.3f}, p = {fixed_results['p_value']:.4f}")
        
        print("\n--- RANDOM-EFFECTS MODEL ---")
        print(f"Pooled Odds Ratio: {random_results['pooled_effect']:.3f}")
        print(f"95% CI: [{random_results['lower_ci']:.3f}, {random_results['upper_ci']:.3f}]")
        print(f"Z = {random_results['z_value']:.3f}, p = {random_results['p_value']:.4f}")
        
        print("\n--- HETEROGENEITY ---")
        het = random_results['heterogeneity']
        print(f"Q = {het['q_statistic']:.2f} (df = {het['df']}), p = {het['p_value']:.4f}")
        print(f"I² = {het['i_squared']:.1f}%")
        print(f"τ² = {het['tau_squared']:.4f}")
        
        # Interpretation
        print("\n--- INTERPRETATION ---")
        if het['i_squared'] < 25:
            print("Low heterogeneity detected")
        elif het['i_squared'] < 50:
            print("Moderate heterogeneity detected")
        elif het['i_squared'] < 75:
            print("Substantial heterogeneity detected")
        else:
            print("Considerable heterogeneity detected")
        
        if random_results['p_value'] < 0.05:
            print("Statistically significant pooled effect (p < 0.05)")
        else:
            print("No statistically significant pooled effect (p ≥ 0.05)")
        
        print("\n" + "="*70)
    
    @staticmethod
    def _normal_cdf(x):
        """Approximate normal CDF"""
        from math import erf, sqrt
        return (1.0 + erf(x / sqrt(2.0))) / 2.0
    
    @staticmethod
    def _chi_square_cdf(x, df):
        """Approximate chi-square CDF using incomplete gamma function"""
        from math import gamma, exp
        
        if x <= 0:
            return 0
        
        # Simple approximation for chi-square CDF
        k = df / 2.0
        x_half = x / 2.0
        
        # Use series expansion for small values
        if x < df + 5 * np.sqrt(df):
            term = exp(-x_half) * (x_half ** k)
            sum_val = term / gamma(k + 1)
            
            for i in range(1, 100):
                term *= x_half / (k + i)
                sum_val += term / gamma(k + i + 1)
                if term < 1e-10:
                    break
            
            return sum_val
        else:
            return 1.0


def main():
    """Example usage"""
    
    # Load extraction results
    with open("meta_analysis_complete.json", 'r') as f:
        results = json.load(f)
    
    # Initialize calculator
    calculator = MetaAnalysisCalculator(results)
    
    # Extract dichotomous outcomes and calculate effect sizes
    print("Extracting effect sizes from studies...")
    calculator.extract_dichotomous_outcomes()
    
    # Perform meta-analyses
    print("\nPerforming meta-analyses...")
    fixed_results = calculator.perform_fixed_effect_meta_analysis()
    random_results = calculator.perform_random_effects_meta_analysis()
    
    # Print summary
    calculator.print_summary(fixed_results, random_results)
    
    # Export results
    calculator.export_results(
        fixed_results,
        random_results,
        output_path="meta_analysis_final.json"
    )
    
    # Show forest plot data
    print("\n--- FOREST PLOT DATA ---")
    forest_data = calculator.generate_forest_plot_data()
    print(forest_data.to_string())


if __name__ == "__main__":
    # Example with simulated data
    print("Meta-Analysis Calculator Example")
    print("-" * 70)
    
    # Simulated extraction results (replace with actual API results)
    sample_results = [
        {
            "document_title": "Study 1",
            "extracted_data": {
                "participants": {
                    "intervention_group_size": 50,
                    "control_group_size": 50
                },
                "outcomes": {
                    "mortality_intervention": 10,
                    "mortality_control": 20
                }
            },
            "citations": [
                {"cited_text": "10 deaths in intervention group", "type": "page_location", "start_page_number": 5},
                {"cited_text": "20 deaths in control group", "type": "page_location", "start_page_number": 5}
            ]
        },
        {
            "document_title": "Study 2",
            "extracted_data": {
                "participants": {
                    "intervention_group_size": 75,
                    "control_group_size": 75
                },
                "outcomes": {
                    "mortality_intervention": 15,
                    "mortality_control": 25
                }
            },
            "citations": [
                {"cited_text": "15 deaths occurred in SDC group", "type": "page_location", "start_page_number": 8},
                {"cited_text": "25 deaths in conservative management", "type": "page_location", "start_page_number": 8}
            ]
        }
    ]
    
    # Run analysis
    calc = MetaAnalysisCalculator(sample_results)
    calc.extract_dichotomous_outcomes()
    
    fixed = calc.perform_fixed_effect_meta_analysis()
    random = calc.perform_random_effects_meta_analysis()
    
    calc.print_summary(fixed, random)
