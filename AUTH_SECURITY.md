# Authentication & Security Guide - Recipe Chatbot

This document outlines a pragmatic security strategy for the Recipe Chatbot application, prioritizing simplicity and effectiveness over complexity.

## Authentication Strategy

### MVP: API Key Authentication

We use simple API key authentication for the initial deployment. This is sufficient for controlling access while keeping implementation straightforward.

```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if not api_key:
        raise HTTPException(status_code=403, detail="API key required")
    
    # In production, fetch from AWS SSM Parameter Store
    valid_api_key = os.getenv("API_KEY")
    
    if api_key != valid_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return api_key

# Usage
@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage, api_key: str = Depends(verify_api_key)):
    return await process_chat(message)
```

### Future: JWT/OAuth2

When we need user accounts, we'll implement JWT authentication. AWS Cognito is an option but adds complexity - evaluate based on actual requirements.



## Input Validation & Prompt Protection

### Basic Input Validation

```python
from pydantic import BaseModel, validator, Field

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    
    @validator('message')
    def clean_message(cls, v):
        # Strip whitespace and control characters
        v = v.strip()
        v = ''.join(char for char in v if ord(char) >= 32)
        
        if not v:
            raise ValueError('Message cannot be empty')
        
        return v
```

### Prompt Injection Protection

Simple pattern matching is sufficient for most cases:

```python
INJECTION_PATTERNS = [
    'ignore previous instructions',
    'disregard all prior',
    'you are now',
    'reveal your instructions',
    'system prompt',
]

def is_safe_message(message: str) -> bool:
    message_lower = message.lower()
    
    # Check for injection patterns
    for pattern in INJECTION_PATTERNS:
        if pattern in message_lower:
            return False
    
    # Check for excessive special characters
    if len(re.findall(r'[<>{}\\]', message)) > 10:
        return False
    
    return True

# In your LangGraph implementation
def create_safe_prompt(user_message: str) -> str:
    """Wrap user input to prevent injection."""
    return f"""You are a helpful cooking assistant. Only answer cooking-related questions.

User question: {user_message}

Provide only cooking-related responses."""
```

## Rate Limiting

### Simple In-Memory Rate Limiting

For MVP, implement basic rate limiting without Redis:

```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, requests_per_hour: int = 100):
        self.requests_per_hour = requests_per_hour
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(hours=1)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.requests_per_hour:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True

rate_limiter = RateLimiter()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    identifier = request.headers.get("X-API-Key", request.client.host)
    
    if not rate_limiter.is_allowed(identifier):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded"}
        )
    
    return await call_next(request)
```

### Production Rate Limiting

Use AWS services for production:

- CloudFront automatically handles most DDoS
- ALB provides connection throttling
- Add WAF only if you experience actual attacks

## CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

# Environment-specific origins
origins = {
    "production": ["https://recipe-chatbot.com"],
    "development": ["http://localhost:3000"]
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins.get(os.getenv("ENVIRONMENT", "development")),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)
```

## Security Headers

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    if os.getenv("ENVIRONMENT") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    
    return response
```

## Secret Management

### Development

Use .env files with python-dotenv:

```
OPENAI_API_KEY=sk-...
SERP_API_KEY=...
API_KEY=your-api-key
```

### Production

Use AWS SSM Parameter Store as outlined in the deployment guide:

```python
import boto3

def get_secret(parameter_name: str) -> str:
    if os.getenv("ENVIRONMENT") == "development":
        return os.getenv(parameter_name)
    
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(
        Name=f"/recipe-chatbot/prod/{parameter_name}",
        WithDecryption=True
    )
    return response['Parameter']['Value']

# Usage
OPENAI_API_KEY = get_secret("openai-api-key")
```

## Security Monitoring

### Basic Logging

```python
import structlog

logger = structlog.get_logger()

# Log security events
@app.middleware("http")
async def security_logging(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    # Log all non-200 responses
    if response.status_code >= 400:
        logger.warning(
            "security_event",
            path=str(request.url.path),
            method=request.method,
            status_code=response.status_code,
            client_ip=request.client.host,
            duration=time.time() - start_time
        )
    
    return response
```

### CloudWatch Alerts

Set up basic alerts in AWS:

- High 4xx error rate (potential attack)
- High 5xx error rate (application issues)
- Unusual traffic patterns

## HTTPS/TLS

Handled automatically by:

- **Development**: Next.js dev server
- **Production**: ALB with ACM certificate

No need to handle TLS in the application.

## Security Checklist

### Before Launch

- [ ] API keys in environment variables or SSM
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] CORS configured for your domain only
- [ ] Security headers added
- [ ] HTTPS enforced in production

### After Launch

- [ ] Monitor CloudWatch logs for anomalies
- [ ] Review rate limit settings based on usage
- [ ] Add WAF if experiencing attacks
- [ ] Implement user authentication when needed

## Incident Response

### If You Detect an Attack

#### Immediate Actions

1. Check CloudWatch logs
2. Temporarily tighten rate limits
3. Block suspicious IPs in security group

#### Investigation

1. Identify attack pattern
2. Check for data exposure
3. Review application logs

#### Recovery

1. Deploy fixes if vulnerabilities found
2. Update security rules
3. Document incident

#### Contact Points

- **AWS Support**: For infrastructure issues
- **Application Team**: For code vulnerabilities
- **Security Team**: For incident coordination

## Summary

This security approach:

- Starts simple with API keys and basic protections
- Avoids over-engineering (no ML models, complex auth)
- Uses AWS managed services where sensible
- Provides clear upgrade path as needs grow
