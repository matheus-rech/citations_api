"""
Streaming Meta-Analysis Data Extractor
Real-time extraction with progressive citation tracking
"""

import anthropic
import base64
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class StreamingCitation:
    """Citation accumulator for streaming responses"""
    text: str = ""
    citations: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_text(self, text: str):
        self.text += text
    
    def add_citation(self, citation: Dict[str, Any]):
        self.citations.append(citation)


class StreamingMetaAnalysisExtractor:
    """Extract meta-analysis data with streaming and real-time feedback"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5"
    
    def load_pdf_as_base64(self, pdf_path: str) -> str:
        """Load PDF and encode as base64"""
        with open(pdf_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def extract_with_streaming(
        self,
        pdf_path: str,
        extraction_schema: Dict[str, Any],
        on_text_callback: Optional[Callable[[str], None]] = None,
        on_citation_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        document_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract data with streaming, providing real-time updates"""
        
        if document_title is None:
            document_title = Path(pdf_path).stem
        
        # Load PDF
        pdf_base64 = self.load_pdf_as_base64(pdf_path)
        
        # Create prompt
        prompt = self._create_extraction_prompt(extraction_schema)
        
        # Accumulate response
        current_block = StreamingCitation()
        all_blocks = []
        full_text = ""
        
        # Stream the response
        with self.client.messages.stream(
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
        ) as stream:
            for event in stream:
                if event.type == "content_block_start":
                    # Start a new content block
                    current_block = StreamingCitation()
                
                elif event.type == "content_block_delta":
                    delta = event.delta
                    
                    if delta.type == "text_delta":
                        # Add text to current block
                        text = delta.text
                        current_block.add_text(text)
                        full_text += text
                        
                        # Callback for real-time text
                        if on_text_callback:
                            on_text_callback(text)
                    
                    elif delta.type == "citations_delta":
                        # Add citation to current block
                        citation = delta.citation
                        current_block.add_citation(citation)
                        
                        # Callback for real-time citation
                        if on_citation_callback:
                            on_citation_callback(citation)
                
                elif event.type == "content_block_stop":
                    # Save completed block
                    all_blocks.append({
                        "text": current_block.text,
                        "citations": current_block.citations
                    })
        
        # Parse the complete JSON response
        extracted_data = self._parse_json_response(full_text)
        
        # Organize all citations
        all_citations = []
        for block in all_blocks:
            all_citations.extend(block["citations"])
        
        return {
            "document_title": document_title,
            "extracted_data": extracted_data,
            "content_blocks": all_blocks,
            "citations": all_citations,
            "citation_count": len(all_citations)
        }
    
    def extract_batch_with_progress(
        self,
        pdf_paths: List[str],
        extraction_schema: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """Extract from multiple papers with progress tracking"""
        
        results = []
        total = len(pdf_paths)
        
        for idx, pdf_path in enumerate(pdf_paths, 1):
            if progress_callback:
                progress_callback(idx, total, f"Processing {Path(pdf_path).name}")
            
            try:
                # Define callbacks for this file
                def on_text(text):
                    if progress_callback:
                        progress_callback(idx, total, f"Extracting... {text[:50]}")
                
                def on_citation(citation):
                    cited_text = citation.get('cited_text', '')[:40]
                    page = citation.get('start_page_number', '?')
                    if progress_callback:
                        progress_callback(
                            idx, total, 
                            f"Citation found (page {page}): {cited_text}..."
                        )
                
                result = self.extract_with_streaming(
                    pdf_path,
                    extraction_schema,
                    on_text_callback=on_text,
                    on_citation_callback=on_citation
                )
                results.append(result)
                
            except Exception as e:
                print(f"\nError processing {pdf_path}: {str(e)}")
                results.append({
                    "error": str(e),
                    "file": pdf_path
                })
        
        return results
    
    def _create_extraction_prompt(self, schema: Dict[str, Any]) -> str:
        """Create extraction prompt"""
        schema_json = json.dumps(schema, indent=2)
        
        return f"""Extract the following data from this research paper for meta-analysis.

Schema:
{schema_json}

CRITICAL INSTRUCTIONS:
1. Use citations to back up EVERY extracted value
2. For numerical data, cite the exact location (page and text) where it appears
3. If a value is not found, use null
4. Return ONLY valid JSON, no additional text
5. Do not include any text outside the JSON structure

Extract the data now, ensuring every field has supporting citations."""
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from response text"""
        try:
            # Remove markdown code blocks
            json_text = text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.startswith("```"):
                json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return {"raw_text": text, "parse_error": str(e)}
    
    def generate_citation_report(
        self,
        results: List[Dict[str, Any]],
        output_path: str = "citation_report.html"
    ):
        """Generate an HTML report showing all citations"""
        
        html_parts = [
            """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Meta-Analysis Citation Report</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .study {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .study-title {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #1a1a1a;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .stat {
            flex: 1;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: 600;
            color: #0066cc;
        }
        .citation {
            border-left: 4px solid #0066cc;
            padding: 12px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .citation-text {
            font-style: italic;
            color: #333;
            margin-bottom: 8px;
        }
        .citation-location {
            font-size: 13px;
            color: #666;
        }
        .section-title {
            font-size: 18px;
            font-weight: 600;
            margin-top: 20px;
            margin-bottom: 10px;
            color: #1a1a1a;
        }
        .data-field {
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 10px;
            padding: 8px;
            border-bottom: 1px solid #eee;
        }
        .field-name {
            font-weight: 500;
            color: #666;
        }
        .field-value {
            color: #1a1a1a;
        }
    </style>
</head>
<body>
    <h1>Meta-Analysis Extraction Report</h1>
    <p>Generated with Anthropic Citations API - Full Provenance Tracking</p>
"""
        ]
        
        for result in results:
            if "error" in result:
                continue
            
            doc_title = result.get("document_title", "Unknown")
            citation_count = result.get("citation_count", 0)
            extracted = result.get("extracted_data", {})
            citations = result.get("citations", [])
            
            html_parts.append(f"""
    <div class="study">
        <div class="study-title">{doc_title}</div>
        <div class="stats">
            <div class="stat">
                <div class="stat-label">Citations</div>
                <div class="stat-value">{citation_count}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Fields Extracted</div>
                <div class="stat-value">{self._count_fields(extracted)}</div>
            </div>
        </div>
        
        <div class="section-title">Extracted Data</div>
""")
            
            # Show extracted fields
            for section, fields in extracted.items():
                if isinstance(fields, dict):
                    html_parts.append(f'<div style="margin-left: 20px; margin-top: 15px;"><strong>{section}</strong></div>')
                    for field, value in fields.items():
                        html_parts.append(f"""
        <div class="data-field">
            <div class="field-name">{field}</div>
            <div class="field-value">{value if value is not None else 'Not found'}</div>
        </div>
""")
            
            # Show citations
            html_parts.append('<div class="section-title">Citations</div>')
            for citation in citations:
                cited_text = citation.get('cited_text', '')
                if citation.get('type') == 'page_location':
                    location = f"Pages {citation.get('start_page_number')}-{citation.get('end_page_number') - 1}"
                else:
                    location = f"Chars {citation.get('start_char_index')}-{citation.get('end_char_index')}"
                
                html_parts.append(f"""
        <div class="citation">
            <div class="citation-text">"{cited_text[:200]}{'...' if len(cited_text) > 200 else ''}"</div>
            <div class="citation-location">📍 {location}</div>
        </div>
""")
            
            html_parts.append('    </div>')
        
        html_parts.append("""
</body>
</html>
""")
        
        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_parts))
        
        print(f"\n📊 Citation report generated: {output_path}")
    
    def _count_fields(self, data: Dict) -> int:
        """Count number of non-null fields"""
        count = 0
        for value in data.values():
            if isinstance(value, dict):
                count += self._count_fields(value)
            elif value is not None:
                count += 1
        return count


def main():
    """Example usage with progress tracking"""
    import sys
    
    extractor = StreamingMetaAnalysisExtractor()
    
    # Define schema
    schema = {
        "study_info": {
            "first_author": "string",
            "year": "integer",
            "sample_size": "integer"
        },
        "outcomes": {
            "mortality_intervention": "integer",
            "mortality_control": "integer",
            "favorable_outcome_intervention": "integer",
            "favorable_outcome_control": "integer"
        }
    }
    
    # Example: Single paper with streaming
    print("=== Streaming Extraction ===\n")
    
    def on_text(text):
        # Print text as it streams
        print(text, end='', flush=True)
    
    def on_citation(citation):
        # Show citation notifications
        page = citation.get('start_page_number', '?')
        sys.stdout.write(f"\n[📌 Citation: page {page}]\n")
        sys.stdout.flush()
    
    pdf_path = "/mnt/user-data/uploads/sample_paper.pdf"
    
    try:
        result = extractor.extract_with_streaming(
            pdf_path,
            schema,
            on_text_callback=on_text,
            on_citation_callback=on_citation
        )
        
        print("\n\n=== Extraction Complete ===")
        print(f"Document: {result['document_title']}")
        print(f"Citations found: {result['citation_count']}")
        print(f"\nExtracted data:")
        print(json.dumps(result['extracted_data'], indent=2))
        
    except FileNotFoundError:
        print(f"File not found: {pdf_path}")
        print("\nTo use this script:")
        print("1. Upload your PDF papers")
        print("2. Update pdf_path to point to your files")
        print("3. Run the script")
    
    # Example: Batch processing with progress
    print("\n\n=== Batch Processing Example ===\n")
    
    pdf_files = [
        "/mnt/user-data/uploads/paper1.pdf",
        "/mnt/user-data/uploads/paper2.pdf",
    ]
    
    def progress_callback(current, total, message):
        percent = (current / total) * 100
        print(f"\r[{current}/{total}] {percent:.0f}% - {message}", end='', flush=True)
    
    # Uncomment to run batch processing:
    # results = extractor.extract_batch_with_progress(
    #     pdf_files,
    #     schema,
    #     progress_callback=progress_callback
    # )
    # 
    # print("\n\n=== Generating Report ===")
    # extractor.generate_citation_report(results, "meta_analysis_report.html")


if __name__ == "__main__":
    main()
