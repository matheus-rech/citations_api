"""
Meta-Analysis Data Extractor with Anthropic Citations API
Extracts structured data from research papers with full provenance tracking
"""

import anthropic
import base64
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import pandas as pd


@dataclass
class Citation:
    """Store citation information"""
    cited_text: str
    document_index: int
    document_title: str
    page_range: Optional[tuple] = None
    char_range: Optional[tuple] = None
    
    @classmethod
    def from_api_citation(cls, citation: Dict[str, Any]) -> 'Citation':
        """Create Citation from API response"""
        if citation['type'] == 'page_location':
            return cls(
                cited_text=citation['cited_text'],
                document_index=citation['document_index'],
                document_title=citation.get('document_title', ''),
                page_range=(citation['start_page_number'], citation['end_page_number'])
            )
        elif citation['type'] == 'char_location':
            return cls(
                cited_text=citation['cited_text'],
                document_index=citation['document_index'],
                document_title=citation.get('document_title', ''),
                char_range=(citation['start_char_index'], citation['end_char_index'])
            )
        else:
            return cls(
                cited_text=citation['cited_text'],
                document_index=citation['document_index'],
                document_title=citation.get('document_title', '')
            )


@dataclass
class ExtractedDataPoint:
    """Single extracted data point with citation"""
    field_name: str
    value: Any
    citations: List[Citation]
    confidence: Optional[str] = None


@dataclass
class StudyData:
    """Structured study data for meta-analysis"""
    study_id: str
    first_author: str
    year: int
    sample_size: int
    intervention: str
    control: str
    outcome_measure: str
    effect_size: Optional[float]
    standard_error: Optional[float]
    ci_lower: Optional[float]
    ci_upper: Optional[float]
    p_value: Optional[float]
    
    # Store all extracted data points with citations
    extracted_fields: List[ExtractedDataPoint] = None
    
    def __post_init__(self):
        if self.extracted_fields is None:
            self.extracted_fields = []


class MetaAnalysisExtractor:
    """Extract meta-analysis data from papers using Citations API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5"
    
    def load_pdf_as_base64(self, pdf_path: str) -> str:
        """Load PDF and encode as base64"""
        with open(pdf_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def create_extraction_prompt(self, extraction_schema: Dict[str, Any]) -> str:
        """Create a prompt for structured data extraction"""
        schema_description = json.dumps(extraction_schema, indent=2)
        
        return f"""You are extracting data from a research paper for meta-analysis.

Extract the following information and provide citations for each piece of data:

{schema_description}

IMPORTANT INSTRUCTIONS:
1. Extract ONLY information that is explicitly stated in the paper
2. For numerical data (sample sizes, effect sizes, p-values, confidence intervals):
   - Extract exact values as reported
   - Include the specific location where each number appears
3. If information is not found, return null for that field
4. Provide your response in valid JSON format
5. Use citations to back up every extracted value

Response format:
{{
  "study_identification": {{
    "first_author": "Author name",
    "year": 2024,
    "study_design": "RCT/Cohort/etc"
  }},
  "participants": {{
    "total_sample_size": 100,
    "intervention_group_size": 50,
    "control_group_size": 50,
    "mean_age": 65.5,
    "percent_male": 60
  }},
  "intervention": {{
    "intervention_description": "Description",
    "control_description": "Description"
  }},
  "outcomes": {{
    "primary_outcome": "Outcome name",
    "intervention_mean": 5.2,
    "intervention_sd": 1.3,
    "control_mean": 3.8,
    "control_sd": 1.1,
    "effect_size": 0.45,
    "confidence_interval_lower": 0.2,
    "confidence_interval_upper": 0.7,
    "p_value": 0.001
  }},
  "quality_assessment": {{
    "randomization": "adequate/inadequate/unclear",
    "blinding": "adequate/inadequate/unclear",
    "follow_up_complete": true/false
  }}
}}

Extract the data now."""
    
    def extract_from_single_paper(
        self,
        pdf_path: str,
        extraction_schema: Optional[Dict[str, Any]] = None,
        document_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract data from a single paper with citations"""
        
        if document_title is None:
            document_title = Path(pdf_path).stem
        
        # Load PDF
        pdf_base64 = self.load_pdf_as_base64(pdf_path)
        
        # Create extraction schema if not provided
        if extraction_schema is None:
            extraction_schema = self._get_default_schema()
        
        # Create prompt
        prompt = self.create_extraction_prompt(extraction_schema)
        
        # Make API call with citations enabled
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64
                            },
                            "title": document_title,
                            "citations": {"enabled": True}
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        # Parse response and extract citations
        return self._parse_response_with_citations(response, document_title)
    
    def extract_from_multiple_papers(
        self,
        pdf_paths: List[str],
        extraction_schema: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Extract data from multiple papers"""
        results = []
        
        for pdf_path in pdf_paths:
            print(f"Processing: {pdf_path}")
            try:
                result = self.extract_from_single_paper(
                    pdf_path,
                    extraction_schema
                )
                results.append(result)
            except Exception as e:
                print(f"Error processing {pdf_path}: {str(e)}")
                results.append({
                    "error": str(e),
                    "file": pdf_path
                })
        
        return results
    
    def _parse_response_with_citations(
        self,
        response: Any,
        document_title: str
    ) -> Dict[str, Any]:
        """Parse API response and extract data with citations"""
        
        # Combine all text and citations
        full_text = ""
        all_citations = []
        text_to_citations = {}  # Map text segments to their citations
        
        for block in response.content:
            if block.type == "text":
                text = block.text
                full_text += text
                
                # Store citations for this text segment if present
                if hasattr(block, 'citations') and block.citations:
                    citations = [Citation.from_api_citation(c) for c in block.citations]
                    text_to_citations[text] = citations
                    all_citations.extend(citations)
        
        # Try to parse as JSON
        try:
            # Remove markdown code blocks if present
            json_text = full_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.startswith("```"):
                json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            extracted_data = json.loads(json_text)
        except json.JSONDecodeError:
            extracted_data = {"raw_text": full_text}
        
        return {
            "document_title": document_title,
            "extracted_data": extracted_data,
            "citations": [asdict(c) for c in all_citations],
            "citation_count": len(all_citations),
            "response": response
        }
    
    def _get_default_schema(self) -> Dict[str, Any]:
        """Get default extraction schema for clinical trials"""
        return {
            "study_identification": {
                "first_author": "string",
                "year": "integer",
                "journal": "string",
                "study_design": "string (RCT, cohort, case-control, etc.)"
            },
            "participants": {
                "total_sample_size": "integer",
                "intervention_group_size": "integer",
                "control_group_size": "integer",
                "mean_age": "float",
                "age_range": "string",
                "percent_male": "float",
                "inclusion_criteria": "string",
                "exclusion_criteria": "string"
            },
            "intervention": {
                "intervention_description": "string",
                "control_description": "string",
                "follow_up_duration": "string"
            },
            "outcomes": {
                "primary_outcome": "string",
                "intervention_mean": "float",
                "intervention_sd": "float",
                "control_mean": "float",
                "control_sd": "float",
                "effect_size": "float",
                "confidence_interval_lower": "float",
                "confidence_interval_upper": "float",
                "p_value": "float"
            }
        }
    
    def export_to_dataframe(
        self,
        results: List[Dict[str, Any]],
        include_citations: bool = True
    ) -> pd.DataFrame:
        """Export extracted data to pandas DataFrame"""
        
        records = []
        for result in results:
            if "error" in result:
                continue
            
            extracted = result.get("extracted_data", {})
            record = {
                "document_title": result.get("document_title", ""),
                "citation_count": result.get("citation_count", 0)
            }
            
            # Flatten nested structure
            for section, fields in extracted.items():
                if isinstance(fields, dict):
                    for field, value in fields.items():
                        record[f"{section}_{field}"] = value
                else:
                    record[section] = fields
            
            if include_citations:
                record["citations"] = json.dumps(result.get("citations", []))
            
            records.append(record)
        
        return pd.DataFrame(records)
    
    def save_results(
        self,
        results: List[Dict[str, Any]],
        output_dir: str = ".",
        prefix: str = "meta_analysis"
    ):
        """Save results in multiple formats"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save complete JSON with citations
        json_path = output_path / f"{prefix}_complete.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Saved complete results to: {json_path}")
        
        # Save as DataFrame
        df = self.export_to_dataframe(results, include_citations=True)
        csv_path = output_path / f"{prefix}_data.csv"
        df.to_csv(csv_path, index=False)
        print(f"Saved tabular data to: {csv_path}")
        
        # Save citation map
        citation_map = {}
        for result in results:
            doc_title = result.get("document_title", "")
            citations = result.get("citations", [])
            citation_map[doc_title] = citations
        
        citation_path = output_path / f"{prefix}_citations.json"
        with open(citation_path, 'w') as f:
            json.dump(citation_map, f, indent=2)
        print(f"Saved citation map to: {citation_path}")


def main():
    """Example usage"""
    
    # Initialize extractor
    extractor = MetaAnalysisExtractor()
    
    # Define custom schema for cerebellar stroke studies
    cerebellar_schema = {
        "study_identification": {
            "first_author": "string",
            "year": "integer",
            "journal": "string",
            "study_design": "string"
        },
        "participants": {
            "total_patients": "integer",
            "sdc_group_size": "integer",
            "conservative_group_size": "integer",
            "mean_age": "float",
            "percent_male": "float"
        },
        "intervention": {
            "surgical_procedure": "string (SDC, cerebellar necrosectomy, EVD, etc.)",
            "timing_of_surgery": "string",
            "conservative_management": "string"
        },
        "outcomes": {
            "mortality_sdc": "integer",
            "mortality_conservative": "integer",
            "favorable_outcome_sdc": "integer (mRS 0-3)",
            "favorable_outcome_conservative": "integer (mRS 0-3)",
            "complications": "string"
        },
        "imaging": {
            "infarct_volume_ml": "float",
            "hydrocephalus_present": "boolean",
            "brainstem_compression": "boolean"
        }
    }
    
    # Example: Process single paper
    pdf_path = "/path/to/paper.pdf"
    result = extractor.extract_from_single_paper(
        pdf_path,
        extraction_schema=cerebellar_schema
    )
    
    print("\n=== Extraction Results ===")
    print(json.dumps(result["extracted_data"], indent=2))
    print(f"\nCitations found: {result['citation_count']}")
    
    # Example: Process multiple papers
    pdf_files = [
        "/path/to/paper1.pdf",
        "/path/to/paper2.pdf",
        "/path/to/paper3.pdf"
    ]
    
    results = extractor.extract_from_multiple_papers(
        pdf_files,
        extraction_schema=cerebellar_schema
    )
    
    # Save all results
    extractor.save_results(results, output_dir="./output", prefix="cerebellar_meta")
    
    # Convert to DataFrame for analysis
    df = extractor.export_to_dataframe(results)
    print("\n=== Extracted Data Summary ===")
    print(df.head())
    print(f"\nTotal studies processed: {len(df)}")


if __name__ == "__main__":
    main()
