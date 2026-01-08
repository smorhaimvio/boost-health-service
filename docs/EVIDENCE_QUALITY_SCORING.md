# Evidence Quality Scoring (0-5 Scale)

## Overview

BoostHealth Service assesses the quality of evidence returned for each search query on a **0-5 scale**. This score helps consumers understand the strength and reliability of the evidence base.

## Scoring Criteria

### Score: 5 - Exceptional
- Multiple systematic reviews or meta-analyses (2+)
- High citation counts (100+ citations)
- Recent evidence (within last 3 years)
- Large result set (5+ papers)

### Score: 4 - Strong
- At least one systematic review or meta-analysis
- Mix of high-quality evidence types
- Good citation counts (50-100 citations)
- Moderate result set (3-5 papers)

### Score: 3 - Moderate
- Several primary studies or reviews
- Decent citation counts
- Mix of evidence types
- Adequate result set (3+ papers)

### Score: 2 - Limited
- Few studies available
- Lower citation counts
- Limited evidence diversity
- Small result set (1-2 papers)

### Score: 1 - Weak
- Very limited evidence
- Low or no citations
- Single study type
- Minimal results

### Score: 0 - Insufficient
- No relevant results found
- Query returned empty result set

## Calculation Logic

The scoring algorithm considers multiple factors:

### 1. Evidence Hierarchy (Most Important)
- **Meta-analyses**: Highest weight (2.5 points for 2+, 2.0 for 1)
- **Systematic Reviews**: High weight (2.0 points for 2+, 1.5 for 1)
- **Randomized Controlled Trials (RCTs)**: Moderate weight (1.5 points for 3+, 1.0 for 1)
- **Other Reviews**: Lower weight (1.0 points for 2+, 0.5 for 1)

### 2. Citation Impact
- **High Citations** (100+): +1.0 points for 2+, +0.5 for 1
- **Moderate Citations** (50-100): +0.5 points for 2+
- Reflects peer validation and research impact

### 3. Result Volume
- **5+ Results**: +1.0 point
- **3-4 Results**: +0.5 points
- More evidence provides better coverage

### 4. Recency Bonus
- **2+ Recent Papers** (within 3 years): +0.5 points
- Ensures evidence is current and relevant

## Example Calculations

### Example 1: High-Quality Query
**Query**: "aspirin cardiovascular prevention systematic review"

**Results**:
- 2 systematic reviews (100+ citations each)
- 3 RCTs (50+ citations each)
- All published within last 3 years

**Calculation**:
- Base (5 results): +1.0
- Evidence hierarchy (2 systematic reviews): +2.0
- Citation impact (2 high-citation): +1.0
- Recency (5 recent): +0.5
- **Total: 4.5 → Score: 5**

### Example 2: Moderate Query
**Query**: "vitamin c antioxidant properties"

**Results**:
- 3 review articles
- 1 with 47 citations, 2 with <25 citations
- Mixed publication years

**Calculation**:
- Base (3 results): +0.5
- Evidence hierarchy (2 reviews): +1.0
- Citation impact (0 high, 1 moderate): +0.0
- Recency: +0.0
- **Total: 1.5 → Score: 2**

### Example 3: Limited Query
**Query**: "obscure compound rare condition"

**Results**:
- 1 case study
- 5 citations
- Published 10 years ago

**Calculation**:
- Base (1 result): +0.0
- Evidence hierarchy (no reviews/RCTs): +0.0
- Citation impact: +0.0
- Recency: +0.0
- **Total: 0 → Score: 0**

## Usage in API Response

The evidence quality score is returned in the search response:

```json
{
  "query": "vitamin c antioxidant",
  "evidence_quality": 2,
  "results": [...]
}
```

## Implementation

The scoring is calculated in `api/services/reranking_service.py` in the `assess_evidence_quality()` method. The algorithm:

1. Analyzes all returned results
2. Categorizes by publication type
3. Evaluates citation counts
4. Checks recency
5. Applies weighted scoring
6. Rounds to nearest integer (0-5)

## Interpretation for Consumers

- **5**: Exceptional evidence base - high confidence in recommendations
- **4**: Strong evidence - good confidence in recommendations
- **3**: Moderate evidence - reasonable confidence with caveats
- **2**: Limited evidence - low confidence, use with caution
- **1**: Weak evidence - very low confidence, supplementary only
- **0**: Insufficient evidence - cannot make evidence-based recommendation

## Future Enhancements

Potential improvements to the scoring algorithm:

1. **Journal Impact Factor**: Weight results from high-impact journals
2. **Study Design Quality**: Assess methodology rigor
3. **Consistency**: Check for conflicting findings
4. **Sample Size**: Consider study population sizes
5. **Domain-Specific**: Adjust weights for different medical domains
6. **Conflict of Interest**: Flag industry-funded studies
