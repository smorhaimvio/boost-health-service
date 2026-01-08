"""API routes for BoostHealth Service."""

from fastapi import APIRouter, HTTPException, status

from api.models import SearchRequest, SearchResponse
from api.core.dependencies import get_bh_core

router = APIRouter(tags=["BoostHealth Intelligence Platform"])


@router.post("/evidence/search", response_model=SearchResponse)
async def evidence_search(request: SearchRequest):
    """
    Search evidence from regulatory, clinical, and policy sources.
    
    Primary endpoint for FM Agent to retrieve structured evidence on demand.
    
    This endpoint performs:
    1. Intent extraction for query optimization
    2. Query encoding with MedCPT embeddings
    3. Vector search across governed knowledge base
    4. Lexical filtering for precision
    5. Hybrid reranking for relevance
    6. Evidence quality assessment
    
    Returns prioritized evidence to support automated healthcare decisions.
    """
    try:
        core = get_bh_core()
        response = await core.search_service.search(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evidence search failed: {str(e)}",
        )


@router.post("/policy/verify")
async def policy_verify():
    """
    Verify policy compliance and coverage criteria.
    
    [NOT YET IMPLEMENTED]
    Future endpoint for policy verification workflows including:
    - Prior authorization criteria checking
    - Formulary verification
    - Coverage policy validation
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Policy verification endpoint not yet implemented",
    )


@router.post("/cds/recommend")
async def cds_recommend():
    """
    Clinical Decision Support recommendations.
    
    [NOT YET IMPLEMENTED]
    Future endpoint for CDS workflows including:
    - Treatment recommendations
    - Drug interaction checks
    - Guideline adherence verification
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="CDS recommendation endpoint not yet implemented",
    )


