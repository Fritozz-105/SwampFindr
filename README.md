# SwampFindr

> AI-powered apartment search for University of Florida students.

CIS4914 Senior Project — Spring 2026
**Team:** Kartik Kathuria, Kausthubh Konuru, Zachary Zeng

---

## Overview

SwampFindr helps UF students find housing that matches their actual needs — budget, distance from campus, pet policies, amenities — using semantic search and a conversational AI agent. Instead of scrolling through generic listing sites, students describe what they want and get personalized results instantly.

---

## Features

| Feature | Description |
|---|---|
| Personalized Recommendations | AI-matched listings based on your onboarding profile |
| Semantic Search | Natural language search with list and map views |
| AI Chat Agent | Ask questions, compare listings, get neighborhood details |
| Tour Scheduling via Email | Agent sends tour requests to landlords through your Gmail |
| Favorites | Bookmark and revisit listings you're interested in |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Framer Motion |
| Auth | Supabase Auth (email/password + Google OAuth) |
| Database | MongoDB Atlas (listings, profiles, chat history) |
| Vector Search | Pinecone (semantic search + user preference embeddings) |
| AI Agent | LangChain, OpenAI, Gmail API |
| Backend | Flask, Flask-RESTX |

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Frontend

```bash
cd swampfindr
npm install
npm run dev
```

Runs at `http://localhost:3000`

### Backend

```bash
cd backend
uv sync
uv run python run.py
```

Runs at `http://localhost:8080`
Swagger docs at `http://localhost:8080/api/v1/docs`

### Environment Variables

Copy `.env.example` to `.env` in both `swampfindr/` and `backend/` and fill in:

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=

# MongoDB
MONGODB_URI=

# Pinecone
PINECONE_API_KEY=

# OpenAI
OPENAI_API_KEY=

# Google OAuth (Gmail integration)
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_GMAIL_REDIRECT_URI=http://localhost:8080/api/v1/emailing/google/callback
```

---

## Project Structure

```
SwampFindr/
├── swampfindr/          # Next.js frontend
│   ├── src/
│   │   ├── app/         # App Router pages (auth, onboarding, home, search, chat, favorites, settings)
│   │   ├── components/  # Shared UI components
│   │   ├── hooks/       # Custom React hooks
│   │   ├── lib/         # Supabase, API clients, Pinecone utilities
│   │   └── types/       # TypeScript type definitions
│   └── public/
├── backend/             # Flask API server
│   ├── app/
│   │   ├── agents/      # LangChain agent, tools, prompts
│   │   ├── database/    # MongoDB connection singleton
│   │   ├── models/      # Pydantic data models
│   │   ├── routes/      # Flask-RESTX API endpoints
│   │   └── services/    # Business logic (Gmail, listings, etc.)
│   ├── scripts/         # Data ingestion and embedding pipelines
│   └── tests/           # Backend test suite
└── docs/                # Project documentation
```

---

## Running Tests

```bash
# Frontend
cd swampfindr && npm run test

# Backend
cd backend && uv run pytest
```

---

## Development Commands

```bash
# Frontend lint
cd swampfindr && npm run lint

# Backend lint + format
cd backend && uv run flake8 app/ && uv run black app/

# Deploy backend to Heroku
git subtree push --prefix backend heroku main
```
