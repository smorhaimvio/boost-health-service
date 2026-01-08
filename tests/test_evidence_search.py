"""Tests for evidence search endpoint."""

import pytest
import httpx


BASE_URL = "http://localhost:8001"
API_KEY = "fm-agent-key-secure-123"


@pytest.mark.asyncio
async def test_evidence_search():
    """Test /evidence/search endpoint returns relevant results."""
    async with httpx.AsyncClient() as client:
        # Test basic search
        response = await client.post(
            f"{BASE_URL}/evidence/search",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "query": "vitamin c antioxidant properties",
                "limit": 3,
                "year_from": 2018,
                "min_citations": 5,
            },
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert data["query"] == "vitamin c antioxidant properties"
        assert len(data["results"]) <= 3
        
        # Check result structure
        if data["results"]:
            result = data["results"][0]
            assert "paper_id" in result
            assert "title" in result
            assert "abstract" in result
            assert "year" in result
            assert "vector_score" in result
            assert "lexical_score" in result
            assert "combined_score" in result
            assert "evidence_quality" in result
            
            # Check evidence quality is 0-5 scale
            assert isinstance(result["evidence_quality"], int)
            assert 0 <= result["evidence_quality"] <= 5
            
            # Check year filter
            assert result["year"] >= 2018
        
        # Test with different query
        response = await client.post(
            f"{BASE_URL}/evidence/search",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "query": "aspirin cardiovascular",
                "limit": 2,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 2


@pytest.mark.asyncio
async def test_authentication():
    """Test authentication requirements for protected endpoints."""
    async with httpx.AsyncClient() as client:
        # Test missing auth header
        response = await client.post(
            f"{BASE_URL}/evidence/search",
            json={"query": "test", "limit": 1},
        )
        assert response.status_code == 401
        assert "Authorization" in response.json()["detail"]
        
        # Test invalid API key
        response = await client.post(
            f"{BASE_URL}/evidence/search",
            headers={"Authorization": "Bearer invalid-key"},
            json={"query": "test", "limit": 1},
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoints are accessible without auth."""
    async with httpx.AsyncClient() as client:
        # Test primary health check
        response = await client.get(f"{BASE_URL}/health_check")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "boosthealth-service"
        assert "version" in data
        
        # Test legacy health check
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_policy_verify():
    """Test /policy/verify endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/policy/verify",
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        # Endpoint not yet implemented
        assert response.status_code == 501
        assert "not yet implemented" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cds_recommend():
    """Test /cds/recommend endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/cds/recommend",
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        # Endpoint not yet implemented
        assert response.status_code == 501
        assert "not yet implemented" in response.json()["detail"].lower()

