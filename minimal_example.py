#!/usr/bin/env python3
"""
Minimal Working Example - Meta-Analysis with Citations API
Extract data from a single PDF and show citations
"""

import anthropic
import base64
import json
import os


def minimal_example():
    """
    Simplest possible example of extracting data with citations
    """
    
    # Setup
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Load PDF
    pdf_path = "sample_paper.pdf"
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf_data = base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"❌ File not found: {pdf_path}")
        print("\nTo run this example:")
        print("1. Place a research paper PDF in the current directory")
        print("2. Rename it to 'sample_paper.pdf' (or update pdf_path variable)")
        print("3. Set ANTHROPIC_API_KEY environment variable")
        print("4. Run: python minimal_example.py")
        return
    
    # Define what to extract
    prompt = """Extract the following from this research paper:

1. First author's last name
2. Publication year
3. Total sample size
4. Number of deaths in intervention group
5. Number of deaths in control group

For EACH piece of data, use citations to show where in the paper you found it.

Return your answer as JSON:
{
  "first_author": "...",
  "year": ...,
  "sample_size": ...,
  "deaths_intervention": ...,
  "deaths_control": ...
}"""
    
    print("\n" + "="*70)
    print("EXTRACTING DATA WITH CITATIONS")
    print("="*70)
    print(f"\nProcessing: {pdf_path}")
    print("\nSending request to Claude...")
    
    # Make API call with citations enabled
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        },
                        "title": pdf_path,
                        "citations": {"enabled": True}  # ← Enable citations!
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    
    # Process response
    print("\n" + "="*70)
    print("EXTRACTION RESULTS")
    print("="*70)
    
    full_text = ""
    citations = []
    
    for block in response.content:
        if block.type == "text":
            full_text += block.text
            
            # Collect citations
            if hasattr(block, 'citations') and block.citations:
                for citation in block.citations:
                    citations.append({
                        "text": citation.cited_text,
                        "page": citation.start_page_number if hasattr(citation, 'start_page_number') else None
                    })
    
    # Parse JSON
    try:
        json_text = full_text.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        
        data = json.loads(json_text.strip())
        
        print("\n📊 Extracted Data:")
        print(json.dumps(data, indent=2))
        
    except json.JSONDecodeError:
        print("\n📄 Raw Response:")
        print(full_text)
        data = None
    
    # Show citations
    print("\n" + "="*70)
    print("CITATIONS (Evidence for Extracted Data)")
    print("="*70)
    
    if citations:
        print(f"\n✅ Found {len(citations)} citations:\n")
        for i, citation in enumerate(citations, 1):
            page = citation['page'] or '?'
            text = citation['text'][:100] + '...' if len(citation['text']) > 100 else citation['text']
            print(f"{i}. Page {page}")
            print(f"   \"{text}\"")
            print()
    else:
        print("\n⚠️  No citations found in response")
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\n✓ Document processed: {pdf_path}")
    print(f"✓ Data extracted: {len(data) if data else 0} fields")
    print(f"✓ Citations tracked: {len(citations)} references")
    print("\n💡 Every data point is now linked to its source location!")
    print("   This provides complete audit trails for systematic reviews.")
    
    return data, citations


def show_citation_provenance_example():
    """
    Show how citations provide provenance
    """
    print("\n" + "="*70)
    print("WHY CITATIONS MATTER FOR META-ANALYSIS")
    print("="*70)
    
    print("""
When you extract data for meta-analysis, you need to verify:
1. Where each number came from
2. What the exact context was
3. How to trace back to the source

Without citations:
❌ "Sample size: 150" - Where did this come from?
❌ "Mortality: 25" - Which group? Which table?
❌ Can't verify during peer review

With citations:
✅ "Sample size: 150" → Page 5, "A total of 150 patients were enrolled"
✅ "Mortality: 25" → Page 12, Table 2, "25 deaths in the SDC group"
✅ Complete audit trail for reviewers and readers

This is crucial for:
- PRISMA-compliant systematic reviews
- Journal submission and peer review
- Reproducible research
- Quality assurance
""")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          Meta-Analysis Data Extraction with Citations            ║
║                    Minimal Working Example                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # Show why this matters
    show_citation_provenance_example()
    
    # Run extraction
    minimal_example()
    
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("""
To use this with your own papers:

1. For single paper:
   python minimal_example.py

2. For multiple papers with full workflow:
   python complete_workflow.py

3. For streaming with progress tracking:
   python streaming_extractor.py

All scripts support custom extraction schemas for any study type!
""")
