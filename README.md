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

### Running with Docker (Recommended)

```bash
# Build and start all services
docker-compose up --build
```

- Backend will be available at http://localhost:8000
- Frontend will be available at http://localhost:3000
- Both services support hot reload for development

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

### Chat Endpoint (Traditional)

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I make scrambled eggs?"}'
```

### Streaming Chat Endpoint (SSE)

```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I make scrambled eggs?"}' \
  --no-buffer
```

The streaming endpoint returns Server-Sent Events with different event types:
- `status`: Processing updates (e.g., "Analyzing your cooking question...")
- `tool`: Tool usage notifications (e.g., "Using web_search tool...")
- `content`: Streaming response content in chunks
- `complete`: Final metadata with tools used, cookware check, etc.
- `error`: Error messages

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
- ✅ **Streaming responses with real-time updates**
- ✅ **Live status updates during processing**
- ⏳ Enhanced UI components (planned)
- ⏳ Markdown support for recipes (planned)

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
- [x] FastAPI structure with traditional and streaming endpoints
- [x] Next.js 15 setup with TypeScript
- [x] LangGraph implementation with conditional workflows
- [x] Tool integrations (query classifier, web search, cookware checker)
- [x] Frontend chat interface with streaming support
- [x] Real-time status updates and visual feedback
- [x] End-to-end functionality

### In Progress
- [ ] Markdown support for recipe formatting
- [ ] Enhanced error handling and retries
- [ ] Unit tests for core components

### Planned
- [ ] shadcn/ui component migration
- [ ] Copy-to-clipboard functionality
- [ ] Recipe card components
- [ ] CI/CD pipeline

## Design Decisions

- **LangGraph over LangChain agents**: Provides more control over decision flow
- **FastAPI**: Fast, type-safe API development with automatic OpenAPI docs
- **Next.js 15 App Router**: Modern React framework with TypeScript support
- **Docker Compose**: Simplified multi-service development environment
- **Server-Sent Events for streaming**: Provides real-time updates without WebSocket complexity
- **Dual API approach**: Both traditional REST and streaming endpoints for flexibility
- **Component-based streaming state**: UI updates reflect real-time processing stages

## Next Steps

1. Implement LangGraph workflow nodes
2. Add web search and cookware validation tools
3. Build chat interface components
4. Connect frontend to backend API
5. Add streaming support
6. Enhance error handling and logging
