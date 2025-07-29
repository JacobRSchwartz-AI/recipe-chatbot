# Recipe Chatbot - AI-Powered Cooking Assistant

An AI-powered recipe chatbot built with FastAPI, LangGraph, and Next.js that helps users with cooking questions, recipe suggestions, and validates recipes against available cookware.

## Project Structure

```
.
├── backend/                 # FastAPI backend with LangGraph
│   ├── main.py             # FastAPI entry point
│   ├── graphs/             # LangGraph nodes and flows
│   ├── tools/              # External tools (SERP, cookware checker)
│   ├── schemas/            # Pydantic models
│   └── Dockerfile
├── frontend/               # Next.js 15 frontend
│   ├── src/
│   │   ├── app/           # App Router pages
│   │   ├── components/    # UI components
│   │   └── lib/          # API clients and utilities
│   └── Dockerfile
├── docker-compose.yml      # Multi-service container setup
└── README.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Environment Setup

1. Copy environment variables:
```bash
cp backend/.env.example backend/.env
```

2. Add your API keys to `backend/.env`:
```
OPENAI_API_KEY=your_openai_key_here
SERP_API_KEY=your_serp_key_here
```

### Running with Docker

```bash
# Build and start all services
docker-compose up --build

# Backend will be available at http://localhost:8000
# Frontend will be available at http://localhost:3000
```

### Running Locally (Development)

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Usage

### Chat Endpoint

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I make scrambled eggs?"}'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Features

- ✅ Query classification (cooking vs non-cooking)
- ✅ LLM-driven tool usage via LangGraph
- ✅ Cookware validation against available tools
- ✅ Web search integration for recipe research
- ✅ Next.js chat interface with TypeScript
- ✅ Docker containerization
- ⏳ Streaming responses (planned)
- ⏳ Enhanced UI components (planned)

## Available Cookware

The system validates recipes against this hardcoded cookware list:
- Spatula
- Frying Pan
- Little Pot
- Stovetop
- Whisk
- Knife
- Ladle
- Spoon

## Development Status

This is a work-in-progress implementation for the AI Engineer assessment. 

### Completed
- [x] Monorepo scaffolding
- [x] Docker setup
- [x] Basic FastAPI structure
- [x] Next.js 15 setup
- [x] Core schemas and models

### In Progress
- [ ] LangGraph implementation
- [ ] Tool integrations
- [ ] Frontend chat interface
- [ ] End-to-end testing

### Planned
- [ ] Streaming responses
- [ ] Enhanced error handling
- [ ] Unit tests
- [ ] CI/CD pipeline

## Design Decisions

- **LangGraph over LangChain agents**: Provides more control over decision flow
- **FastAPI**: Fast, type-safe API development with automatic OpenAPI docs
- **Next.js 15 App Router**: Modern React framework with TypeScript support
- **Docker Compose**: Simplified multi-service development environment

## Next Steps

1. Implement LangGraph workflow nodes
2. Add web search and cookware validation tools
3. Build chat interface components
4. Connect frontend to backend API
5. Add streaming support
6. Enhance error handling and logging
