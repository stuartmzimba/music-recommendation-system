# Music Recommender API Documentation

## Overview

The Music Recommender API provides endpoints for getting personalized music recommendations using a hybrid approach combining Apriori association rules, content-based filtering, and popularity-based recommendations.

**Base URL**: `http://localhost:8000` (development) or your deployed URL
**API Version**: v1
**Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

## Authentication

Currently, the API does not require authentication. For production deployment, consider implementing:
- API key authentication
- OAuth 2.0
- Rate limiting

## Endpoints

### Health Check

#### GET `/health`

Check the health status of the API.

**Response**:
```json
{
  "status": "healthy",
  "service": "music-recommender-api"
}
```

### Root Endpoint

#### GET `/`

Get basic API information.

**Response**:
```json
{
  "message": "Music Recommender API",
  "version": "1.0.0"
}
```

### Get Recommendations

#### POST `/api/v1/recommend`

Get personalized music recommendations using hybrid approach.

**Request Body**:
```json
{
  "basket": ["Master KG", "Amapiano", "Tyla"],
  "genres": ["amapiano", "afrobeats"],
  "user_id": "user123",
  "top_k": 10
}
```

**Parameters**:
- `basket` (required): Array of favorite songs or artists
- `genres` (optional): Array of preferred genres
- `user_id` (optional): User identifier for personalization
- `top_k` (optional): Number of recommendations (1-50, default: 10)

**Response**:
```json
[
  {
    "track_name": "Jerusalema",
    "artist": "Master KG",
    "score": 0.95,
    "reason": "apriori",
    "genre": "amapiano",
    "spotify_id": "2DlHlPMa4M17kufBvI2lEN"
  },
  {
    "track_name": "Water",
    "artist": "Tyla",
    "score": 0.88,
    "reason": "content_based",
    "genre": "amapiano",
    "spotify_id": "4aVuWgvD0X63hcOCnZtNFA"
  }
]
```

**Recommendation Reasons**:
- `apriori`: Based on association rules from user listening patterns
- `content_based`: Based on song features and metadata similarity
- `popular`: Based on popularity in South Africa

### Get Popular Songs

#### GET `/api/v1/popular`

Get popular songs in South Africa.

**Query Parameters**:
- `limit` (optional): Number of songs to return (default: 20)
- `genre` (optional): Filter by specific genre

**Example**: `/api/v1/popular?limit=10&genre=amapiano`

**Response**:
```json
[
  {
    "track_name": "Jerusalema",
    "artist": "Master KG",
    "popularity_score": 0.95,
    "genre": "amapiano",
    "spotify_id": "2DlHlPMa4M17kufBvI2lEN"
  }
]
```

### Get Available Genres

#### GET `/api/v1/genres`

Get list of available music genres.

**Response**:
```json
{
  "genres": ["amapiano", "afrobeats", "gqom", "hip-hop"]
}
```

### Get Popular Artists

#### GET `/api/v1/artists`

Get list of popular artists.

**Query Parameters**:
- `limit` (optional): Number of artists to return (default: 50)

**Response**:
```json
{
  "artists": ["Master KG", "Burna Boy", "Tyla", "Kabza De Small"]
}
```

## Error Handling

The API uses standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `422`: Validation Error (invalid request body)
- `500`: Internal Server Error

**Error Response Format**:
```json
{
  "detail": "Error description"
}
```

**Validation Error Example**:
```json
{
  "detail": [
    {
      "loc": ["body", "top_k"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge",
      "ctx": {"limit_value": 1}
    }
  ]
}
```

## Rate Limiting

For production deployment, implement rate limiting:
- 100 requests per minute per IP
- 1000 requests per hour per user
- Burst allowance for short spikes

## Caching

The API implements caching for improved performance:
- Recommendation results cached for 1 hour
- Popular songs cached for 24 hours
- Cache invalidation on model updates

## Data Models

### RecommendationRequest

```json
{
  "basket": ["string"],
  "genres": ["string"] | null,
  "user_id": "string" | null,
  "top_k": 10
}
```

### RecommendationResponse

```json
{
  "track_name": "string",
  "artist": "string",
  "score": 0.95,
  "reason": "apriori" | "content_based" | "popular",
  "genre": "string" | null,
  "spotify_id": "string" | null
}
```

### PopularSongsResponse

```json
{
  "track_name": "string",
  "artist": "string",
  "popularity_score": 0.95,
  "genre": "string" | null,
  "spotify_id": "string" | null
}
```

## Usage Examples

### Python

```python
import requests

# Get recommendations
response = requests.post(
    "http://localhost:8000/api/v1/recommend",
    json={
        "basket": ["Master KG", "Amapiano"],
        "genres": ["amapiano"],
        "top_k": 5
    }
)
recommendations = response.json()

# Get popular songs
response = requests.get(
    "http://localhost:8000/api/v1/popular?limit=10"
)
popular_songs = response.json()
```

### JavaScript

```javascript
// Get recommendations
const response = await fetch('http://localhost:8000/api/v1/recommend', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    basket: ['Master KG', 'Amapiano'],
    genres: ['amapiano'],
    top_k: 5
  })
});
const recommendations = await response.json();
```

### cURL

```bash
# Get recommendations
curl -X POST "http://localhost:8000/api/v1/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "basket": ["Master KG", "Amapiano"],
    "genres": ["amapiano"],
    "top_k": 5
  }'

# Get popular songs
curl "http://localhost:8000/api/v1/popular?limit=10"
```

## Performance

**Expected Response Times**:
- Recommendations: < 500ms
- Popular songs: < 100ms
- Genres/Artists: < 50ms

**Throughput**:
- 100+ requests per second (single instance)
- Horizontal scaling supported

## Monitoring

Monitor these metrics:
- Response time percentiles (p50, p95, p99)
- Error rate by endpoint
- Cache hit ratio
- Database query performance
- Recommendation algorithm distribution

## Support

For API support:
- Check the interactive documentation at `/docs`
- Review error messages and status codes
- Check system health at `/health`
- Monitor logs for detailed error information
