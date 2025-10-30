# Data Extraction Validation: Multi-Agent & Quality Assurance Proposal

## Problem Statement

**Current State**: Single-pass extraction with no validation
- ❌ No confidence scoring
- ❌ No discrepancy detection
- ❌ No quality checks
- ❌ Extraction errors propagate through entire pipeline

**Impact**: Poor extraction quality undermines meta-analysis validity, especially for:
- Numerical data (sample sizes, outcomes)
- Effect estimates (OR, RR, p-values)
- Study characteristics (design, bias assessment)

---

## Proposed Solutions (Multiple Strategies)

### Strategy 1: Multi-Agent Consensus Extraction ⭐ RECOMMENDED

**Concept**: Multiple independent agents extract same data, then reconcile differences

```
Paper → Agent 1 (Extract) ─┐
Paper → Agent 2 (Extract) ─┼→ Consensus Judge → Validated Data
Paper → Agent 3 (Extract) ─┘
```

**Benefits**:
- Mimics traditional systematic review process (2+ independent reviewers)
- Catches extraction errors through disagreement
- Provides confidence scores based on agreement
- Reduces bias from single extraction

**Implementation**:
```python
class MultiAgentExtractor:
    def __init__(self, num_agents=3):
        self.agents = [MetaAnalysisExtractor() for _ in range(num_agents)]
        self.judge = ConsensusJudge()

    def extract_with_consensus(self, pdf_path, schema):
        # 1. Each agent extracts independently
        extractions = []
        for i, agent in enumerate(self.agents):
            result = agent.extract_from_single_paper(pdf_path, schema)
            result['agent_id'] = i
            extractions.append(result)

        # 2. Compare extractions
        discrepancies = self._find_discrepancies(extractions)

        # 3. Resolve with consensus judge
        consensus = self.judge.resolve_discrepancies(
            extractions=extractions,
            discrepancies=discrepancies,
            pdf_path=pdf_path,
            schema=schema
        )

        return consensus
```

**Consensus Rules**:
- **Full agreement (3/3)**: High confidence, accept immediately
- **Majority agreement (2/3)**: Medium confidence, flag for review
- **No agreement (0/3)**: Low confidence, require manual review
- **Numerical discrepancies**: Use median, flag if variance > threshold

---

### Strategy 2: LLM Judge for Quality Assessment ⭐ RECOMMENDED

**Concept**: Separate LLM evaluates extraction quality against source document

```
Extraction Result → LLM Judge → Quality Score + Issues
     +                            ↓
Original PDF ──────────────→ Suggested Corrections
```

**Judge Responsibilities**:
1. **Citation Verification**: Check if citations support extracted values
2. **Completeness**: Identify missing fields
3. **Logical Consistency**: Detect impossible values (e.g., events > sample size)
4. **Citation Quality**: Rate citation specificity (page vs. sentence-level)

**Implementation**:
```python
class ExtractionQualityJudge:
    def evaluate_extraction(self, extraction_result, pdf_path, schema):
        prompt = f"""You are a quality control judge for data extraction.

        Review this extraction and assess:
        1. Citation Support: Does each citation actually support the extracted value?
        2. Completeness: Are all required fields extracted?
        3. Logical Consistency: Are values internally consistent?
        4. Citation Quality: Are citations specific enough?

        Extraction: {extraction_result}

        Return JSON with:
        {{
            "overall_quality_score": 0-100,
            "field_scores": {{"field_name": score}},
            "issues_found": [
                {{"field": "...", "issue": "...", "severity": "critical|warning|info"}}
            ],
            "suggested_corrections": [...]
        }}
        """

        # Send to Claude with original PDF
        quality_report = self.client.messages.create(
            model="claude-sonnet-4-5",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "document", "source": {...}, "citations": {"enabled": True}},
                    {"type": "text", "text": prompt}
                ]
            }]
        )

        return self._parse_quality_report(quality_report)
```

---

### Strategy 3: Confidence Scoring Per Field

**Concept**: Each extracted field gets a confidence score based on multiple factors

**Confidence Factors**:
1. **Citation Quality** (40%):
   - Specific citation (page + table/figure): 100%
   - Page-level citation only: 70%
   - No citation: 0%

2. **Value Consistency** (30%):
   - Matches expected data type: +30%
   - Within reasonable range: +20%
   - Logical consistency with other fields: +10%

3. **Extraction Context** (30%):
   - Found in expected section (Methods, Results): +30%
   - Multiple supporting citations: +20%
   - Explicit vs. inferred: explicit +30%, inferred +10%

**Implementation**:
```python
@dataclass
class ConfidentExtractedField:
    field_name: str
    value: Any
    citations: List[Citation]
    confidence_score: float  # 0-100
    confidence_breakdown: Dict[str, float]
    needs_review: bool

def calculate_field_confidence(field, extraction_context):
    scores = {
        'citation_quality': _score_citation_quality(field.citations),
        'value_consistency': _score_value_consistency(field.value, field.field_name),
        'extraction_context': _score_extraction_context(extraction_context)
    }

    total = (
        scores['citation_quality'] * 0.4 +
        scores['value_consistency'] * 0.3 +
        scores['extraction_context'] * 0.3
    )

    return ConfidentExtractedField(
        field_name=field.field_name,
        value=field.value,
        citations=field.citations,
        confidence_score=total,
        confidence_breakdown=scores,
        needs_review=(total < 70)  # Flag low-confidence fields
    )
```

---

### Strategy 4: Cross-Validation with Re-Extraction

**Concept**: Re-extract fields with low confidence scores or discrepancies

```
Initial Extraction → Confidence Check → Low Confidence?
                                              ↓ YES
                          Re-extract with targeted prompt
                                              ↓
                          Compare → Accept if consistent
```

**Implementation**:
```python
def validate_and_re_extract(extraction_result, pdf_path, schema):
    low_confidence_fields = [
        field for field in extraction_result['fields']
        if field.confidence_score < 70
    ]

    if not low_confidence_fields:
        return extraction_result  # All good!

    # Re-extract low-confidence fields with targeted prompts
    for field in low_confidence_fields:
        targeted_prompt = f"""Focus specifically on extracting: {field.field_name}

        Previous extraction found: {field.value}
        Citation: {field.citations[0].cited_text if field.citations else "None"}

        Please verify this value or provide the correct value with a specific citation.
        """

        re_extracted = extract_single_field(pdf_path, targeted_prompt)

        # Compare
        if re_extracted.value == field.value:
            field.confidence_score += 20  # Confirmed
        else:
            field.needs_manual_review = True
            field.alternative_value = re_extracted.value

    return extraction_result
```

---

### Strategy 5: Automatic Outlier Detection

**Concept**: Flag statistical outliers that may indicate extraction errors

**Checks**:
1. **Sample size outliers**: > 3 SD from mean
2. **Effect size outliers**: OR < 0.01 or > 100
3. **Impossible values**:
   - Events > sample size
   - Percentages > 100
   - Negative counts
4. **Study characteristic outliers**:
   - Mean age < 0 or > 120
   - Follow-up duration = 0

**Implementation**:
```python
class OutlierDetector:
    def detect_outliers(self, extraction_results):
        issues = []

        # Check each study
        for study in extraction_results:
            # Sample size check
            if study.intervention_group_size + study.control_group_size != study.total_sample_size:
                issues.append({
                    'study': study.study_id,
                    'field': 'sample_size',
                    'issue': 'Sample size mismatch',
                    'severity': 'critical'
                })

            # Events > sample size
            if study.mortality_intervention > study.intervention_group_size:
                issues.append({
                    'study': study.study_id,
                    'field': 'mortality_intervention',
                    'issue': f'Events ({study.mortality_intervention}) > Sample size ({study.intervention_group_size})',
                    'severity': 'critical'
                })

            # Impossible percentages
            if study.percent_male > 100:
                issues.append({
                    'study': study.study_id,
                    'field': 'percent_male',
                    'issue': f'Percentage > 100: {study.percent_male}',
                    'severity': 'critical'
                })

        # Cross-study outliers
        sample_sizes = [s.total_sample_size for s in extraction_results]
        mean_ss = np.mean(sample_sizes)
        std_ss = np.std(sample_sizes)

        for study in extraction_results:
            z_score = (study.total_sample_size - mean_ss) / std_ss
            if abs(z_score) > 3:
                issues.append({
                    'study': study.study_id,
                    'field': 'total_sample_size',
                    'issue': f'Statistical outlier (z={z_score:.2f})',
                    'severity': 'warning'
                })

        return issues
```

---

### Strategy 6: Human-in-the-Loop Verification

**Concept**: Interactive validation for critical fields or low-confidence extractions

```python
class InteractiveValidator:
    def validate_with_human_review(self, extraction_results):
        for study in extraction_results:
            # Show fields needing review
            review_needed = [f for f in study.fields if f.needs_review]

            if not review_needed:
                continue

            print(f"\n{'='*70}")
            print(f"Study: {study.study_id}")
            print(f"{'='*70}")

            for field in review_needed:
                print(f"\nField: {field.field_name}")
                print(f"Extracted value: {field.value}")
                print(f"Confidence: {field.confidence_score:.1f}%")

                if field.citations:
                    print(f"Citation: Page {field.citations[0].start_page_number}")
                    print(f'  "{field.citations[0].cited_text}"')

                # Prompt user
                response = input("\n[A]ccept / [C]orrect / [S]kip? ")

                if response.upper() == 'C':
                    new_value = input("Enter correct value: ")
                    field.value = new_value
                    field.manually_corrected = True
                elif response.upper() == 'A':
                    field.manually_verified = True

        return extraction_results
```

---

## Recommended Implementation: Hybrid Approach

**Phase 1: Multi-Agent Extraction** (Parallel)
```
Paper → [Agent 1, Agent 2, Agent 3] → 3 independent extractions
```

**Phase 2: Consensus + Confidence Scoring**
```
3 extractions → Consensus Judge → Merged result with confidence scores
```

**Phase 3: Quality Assessment**
```
Merged result → LLM Judge → Quality report + issues
```

**Phase 4: Targeted Re-Extraction**
```
Low confidence fields → Re-extract → Update result
```

**Phase 5: Outlier Detection**
```
All studies → Outlier Detector → Flag statistical issues
```

**Phase 6: Human Review (Optional)**
```
Flagged fields → Interactive Validator → Final verified result
```

---

## Validation Metrics to Track

```python
@dataclass
class ExtractionValidationMetrics:
    study_id: str

    # Agreement metrics
    agent_agreement_rate: float  # % fields with full agreement
    high_confidence_fields: int  # Fields with confidence > 80%
    low_confidence_fields: int   # Fields with confidence < 70%

    # Quality metrics
    citation_coverage: float  # % fields with citations
    citation_quality_score: float  # Average citation specificity
    logical_consistency_score: float

    # Issue tracking
    critical_issues: List[str]
    warnings: List[str]

    # Review status
    requires_manual_review: bool
    manually_verified_fields: int
```

---

## Cost-Benefit Analysis

### Multi-Agent Approach (3 agents)
**Costs**:
- 3x API calls per paper
- 1x judge API call
- ~4x total extraction cost

**Benefits**:
- Catches ~80-90% of extraction errors
- High confidence in final results
- Suitable for high-stakes systematic reviews

**When to use**: Cochrane reviews, clinical guidelines, regulatory submissions

---

### Single Agent + LLM Judge
**Costs**:
- 1x extraction API call
- 1x judge API call
- ~2x total extraction cost

**Benefits**:
- Catches ~60-70% of extraction errors
- Good balance of cost/quality
- Faster than multi-agent

**When to use**: Exploratory meta-analyses, preliminary reviews, budget constraints

---

### Confidence Scoring Only
**Costs**:
- 1x extraction API call
- Minimal compute for scoring
- ~1.1x total extraction cost

**Benefits**:
- Identifies uncertain fields
- Guides manual review efforts
- Very fast

**When to use**: High-volume extraction, initial screening, low-risk analyses

---

## Implementation Priority

### Phase 1 (High Impact, Easy)
1. ✅ Confidence scoring per field
2. ✅ Outlier detection
3. ✅ Citation quality scoring

### Phase 2 (High Impact, Moderate)
4. ✅ LLM judge for quality assessment
5. ✅ Targeted re-extraction for low-confidence fields

### Phase 3 (Highest Quality, Higher Cost)
6. ✅ Multi-agent consensus extraction
7. ✅ Interactive validation UI

---

## Code Structure

```
validation/
├── multi_agent_extractor.py      # Multi-agent consensus
├── quality_judge.py               # LLM-based quality assessment
├── confidence_scorer.py           # Per-field confidence calculation
├── outlier_detector.py            # Statistical outlier detection
├── re_extractor.py                # Targeted re-extraction
├── interactive_validator.py       # Human-in-the-loop UI
└── validation_metrics.py          # Metrics tracking
```

---

## Example Usage

```python
from validation import MultiAgentExtractor, QualityJudge, OutlierDetector

# High-quality extraction with validation
extractor = MultiAgentExtractor(num_agents=3)

# Extract with consensus
result = extractor.extract_with_consensus(
    pdf_path="paper.pdf",
    schema=clinical_trial_schema
)

# Quality assessment
judge = QualityJudge()
quality_report = judge.evaluate_extraction(result, "paper.pdf")

# Outlier detection across all studies
detector = OutlierDetector()
outliers = detector.detect_outliers([result1, result2, result3])

# Report
print(f"Extraction confidence: {result.overall_confidence:.1f}%")
print(f"Quality score: {quality_report.overall_quality_score}/100")
print(f"Issues found: {len(quality_report.issues_found)}")
print(f"Outliers detected: {len(outliers)}")

if result.overall_confidence > 90 and quality_report.overall_quality_score > 85:
    print("✅ High-quality extraction - safe to proceed")
else:
    print("⚠️  Manual review recommended")
```

---

## Conclusion

**Recommended Approach**: **Hybrid validation with progressive quality gates**

1. **Default mode**: Single agent + confidence scoring + outlier detection (fast, cheap)
2. **High-stakes mode**: Multi-agent + LLM judge + re-extraction (thorough, expensive)
3. **Interactive mode**: Any mode + human validation (publication-grade)

This provides flexibility based on use case while maintaining quality standards for systematic reviews.

**Next Steps**:
1. Implement Phase 1 (confidence + outliers) - immediate value
2. Test with sample papers - validate effectiveness
3. Implement Phase 2 (LLM judge) - major quality improvement
4. Implement Phase 3 (multi-agent) - for critical applications
