# BH Service - Biomedical Search API

A secure FastAPI service providing biomedical literature search capabilities using MedCPT embeddings, Qdrant vector database, and Grok LLM integration.

## Architecture

BH Service is a standalone microservice that provides:
- **Semantic Search**: MedCPT-based vector search over 7.4M biomedical papers
- **Hybrid Reranking**: Combines vector similarity, lexical matching, and metadata
- **Grok Integration**: LLM-powered tool calling for intelligent search
- **RESTful API**: Simple HTTP API with authentication

## Installation

### 1. Create Virtual Environment

```bash
cd /Users/smorhaim/Sites/fm4/bh/service
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

#### Multi-Client Configuration

BH Service supports multiple clients, each with their own:
- API key for authentication
- Qdrant instance URL
- Qdrant API key
- Collection name

Each client is configured with a prefix (e.g., `FUNCTIONALMIND_`, `AMEDEX_`):

```bash
# Client configuration pattern
<CLIENT_NAME>_API_KEY=client_api_key
<CLIENT_NAME>_QDRANT_URL=https://client-qdrant.cloud.qdrant.io:6333
<CLIENT_NAME>_QDRANT_APIKEY=client_qdrant_api_key
<CLIENT_NAME>_QDRANT_COLLECTION=client_collection_name
```

Configured clients:
- FUNCTIONALMIND - FunctionalMind platform (Active)
- AMEDEX - Amedex healthcare system (Placeholder)
- OLELIFE - OleLife wellness platform (Placeholder)
- TIMELESS_BIOTECH - Timeless Biotech research (Placeholder)
- MYHEALTH_RK - MyHealth RK clinical system (Placeholder)

#### Adding a New Client

1. Generate secure API key: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
2. Add configuration to `.env`:
   ```bash
   NEWCLIENT_API_KEY=generated_key_here
   NEWCLIENT_QDRANT_URL=https://newclient-qdrant.cloud.qdrant.io:6333
   NEWCLIENT_QDRANT_APIKEY=newclient_qdrant_key
   NEWCLIENT_QDRANT_COLLECTION=newclient_collection
   ```
3. Add API key to `API_KEYS` list
4. Restart service

#### Testing Client Access

```bash
curl -X POST http://localhost:8001/evidence/search \
  -H "Authorization: Bearer <CLIENT_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"query": "vitamin c", "limit": 5}'
```

#### Legacy Configuration

For backward compatibility, the service also supports a single shared configuration:
- `API_KEYS`: Comma-separated list of valid API keys
- `QDRANT_URL`: Qdrant cloud URL
- `QDRANT_APIKEY`: Qdrant API key
- `QDRANT_COLLECTION_NAME`: Collection name

Note: Per-client configurations take precedence over legacy settings.

## Running the Service

### Development

```bash
python -m api.main
```

or

```bash
uvicorn api.main:app --reload --port 8001
```

### Production

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8001 --workers 4
```

## API Endpoints

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "bh-service",
  "version": "1.0.0"
}
```

### Search

```bash
POST /api/v1/search
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "query": "vitamin C immune function",
  "limit": 5,
  "year_from": 2018,
  "min_citations": 5,
  "lexical_min": 0.05
}
```

Response:
```json
{
  "query": "vitamin C immune function",
  "results": [
    {
      "paper_id": "12345",
      "title": "Vitamin C and immune function",
      "abstract": "...",
      "authors": ["Smith J", "Doe A"],
      "year": 2020,
      "citation_count": 150,
      "vector_score": 0.89,
      "lexical_score": 0.65,
      "combined_score": 0.82
    }
  ],
  "total_found": 5,
  "evidence_quality": "strong",
  "search_time_ms": 234.5
}
```

### Stream Search

```bash
POST /api/v1/search/stream
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "query": "insulin resistance treatment",
  "limit": 5
}
```

Returns Server-Sent Events (SSE) stream.

### Grok Stream

```bash
POST /api/v1/grok/stream
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "What is vitamin C used for?"}
  ],
  "system_prompt": "You are a medical research assistant.",
  "model": "grok-4-fast-non-reasoning",
  "stream": true
}
```

Returns SSE stream with Grok responses and tool call results.

## Authentication

All endpoints (except `/health`) require Bearer token authentication:

```
Authorization: Bearer YOUR_API_KEY
```

Configure valid API keys in `.env`:
```bash
API_KEYS=key1,key2,key3
```

## Architecture Details

### Components

- **MedCPT Encoder**: Specialized biomedical text embeddings
- **Qdrant Manager**: Vector database client with connection pooling
- **Search Service**: Orchestrates search workflow
- **Reranking Service**: Hybrid scoring algorithm
- **Grok Service**: LLM integration with automatic tool calling

### Search Pipeline

1. **Query Encoding**: Convert text to 768-dim vector with MedCPT
2. **Vector Search**: Find semantically similar papers in Qdrant
3. **Lexical Filtering**: Filter by keyword overlap (configurable threshold)
4. **Hybrid Reranking**: Combine vector, lexical, and metadata scores
5. **Evidence Assessment**: Flag quality (strong/limited)

### Scoring Algorithm

```python
combined_score = vector_score + 0.2 * (lexical_score + metadata_bonus)

metadata_bonus = (
    0.2 if year >= 2022 else 0.1 if year >= 2018 else 0.0
) + (
    0.2 if citations >= 50 else 0.1 if citations >= 10 else 0.0
)
```

## Development

### Project Structure

```
api/
├── api/              # API routes
├── core/             # Configuration and dependencies
├── services/         # Business logic
├── vector_db/        # Qdrant and MedCPT
├── models.py         # Pydantic models
└── main.py           # FastAPI app
```

### Testing

```bash
pytest tests/ -v
```

## Deployment

### Docker (TODO)

```bash
docker build -t bh-service .
docker run -p 8001:8001 --env-file .env bh-service
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Service port | `8001` |
| `DEBUG` | Debug mode | `false` |
| `API_KEYS` | Valid API keys (comma-separated) | Required |
| `XAI_API_KEY` | XAI API key | Required |
| `QDRANT_URL` | Qdrant URL | Required |
| `QDRANT_APIKEY` | Qdrant API key | Required |
| `QDRANT_COLLECTION_NAME` | Collection name | `fm_papers` |
| `ALLOWED_ORIGINS` | CORS origins | `*` |

## Security

- API key authentication required for all endpoints
- CORS configured for allowed origins
- Request validation with Pydantic
- Rate limiting (TODO)
- Request logging for audit

## Performance

- Async/await throughout
- Connection pooling for Qdrant
- Streaming responses for large results
- Configurable timeouts
- MedCPT model cached in memory

## License

Proprietary - Internal use only
