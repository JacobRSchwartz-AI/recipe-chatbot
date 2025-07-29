# Recipe Chatbot - AI-Powered Cooking Assistant

An AI-powered recipe chatbot built with FastAPI, LangGraph, and Next.js that helps users with cooking questions, recipe suggestions, and validates recipes against available cookware.

## Project Structure

```
.
├── backend/                 # FastAPI backend with LangGraph
│   ├── main.py             # FastAPI entry point
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variables template
│   ├── graphs/             # LangGraph nodes and flows
│   │   ├── __init__.py
│   │   └── recipe_graph.py
│   ├── tools/              # External tools (SERP, cookware checker)
│   │   ├── __init__.py
│   │   ├── cookware_checker.py
│   │   ├── query_classifier.py
│   │   └── web_search.py
│   ├── schemas/            # Pydantic models
│   │   └── models.py
│   └── Dockerfile
├── frontend/               # Next.js 15 frontend
│   ├── package.json        # Node.js dependencies
│   ├── next.config.ts      # Next.js configuration
│   ├── tailwind.config.js  # Tailwind CSS configuration
│   ├── tsconfig.json       # TypeScript configuration
│   ├── src/
│   │   ├── app/           # App Router pages
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   ├── components/    # UI components
│   │   │   ├── AnimatedDots.tsx
│   │   │   ├── ChatContainer.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── LoadingIndicator.tsx
│   │   │   ├── MarkdownMessage.tsx
│   │   │   └── MessageBubble.tsx
│   │   ├── hooks/         # Custom React hooks
│   │   │   └── useChat.ts
│   │   └── lib/          # API clients and utilities
│   │       ├── api.ts
│   │       ├── types.ts
│   │       └── utils.ts
│   └── Dockerfile
├── docker-compose.yml      # Multi-service container setup
├── .env.example           # Root environment variables template
├── .gitignore             # Git ignore rules
├── LICENSE                # Project license
├── AUTH_SECURITY.md       # Authentication and security documentation
├── DEPLOYMENT.md          # Deployment strategy documentation
├── ELT_ANALYTICS.md       # Analytics and ELT documentation
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
- ✅ Streaming responses with real-time updates
- ✅ Live status updates during processing

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
- [X] Copy-to-clipboard functionality


## Additional Documentation

The following documentation files provide detailed implementation plans for production deployment:

- **`DEPLOYMENT.md`** - AWS deployment strategy, compute choices, secret management, observability, and scaling considerations
- **`AUTH_SECURITY.md`** - Authentication methods, API security, CORS, rate limiting, input validation, and prompt injection mitigation strategies  
- **`ELT_ANALYTICS.md`** - ELT system design for capturing recipe usage metrics and converting them to business intelligence for stakeholders

## Development Notes

### Time Allocation & Process
This project was developed over the course of the 3-hour assessment timebox with the following progression:

1. **Planning Phase** - Initial project planning and architecture decisions
2. **Backend Development** - Implemented LangGraph-based recipe chatbot with FastAPI endpoints
3. **Basic Frontend** - Created Next.js chat interface with TypeScript and Tailwind CSS
4. **Dockerization** - Added Docker support for both backend and frontend with docker-compose
5. **Markdown Rendering Issues** - Probably slightly too much time spent troubleshooting markdown rendering in the chat interface (partially resolved but still has visual issues)
6. **Documentation Break** - Paused development to create the requested planning documents (DEPLOYMENT.md, AUTH_SECURITY.md, ELT_ANALYTICS.md)
7. **Final UI improvements** - Made additional attempts to improve markdown rendering, animated dots, and copy to clipboard

### Tools Used
- **Visual Studio Code** - Primary development environment
- **Claude 4 Sonnet** - AI assistant for code generation, problem-solving, and architectural guidance throughout the development process

### Known Issues & Trade-offs
- Markdown rendering in chat bubbles works functionally but has poor visual formatting
- Limited time prevented full polish of the UI/UX
- Some edge cases in recipe validation remain unhandled
- Would like to add a CI/CD pipeline, linting, etc.
