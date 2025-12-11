# 🍲 Sarma - Forecast Health Platform

**AI-Powered Nutrition & Health Tracking Platform**

A full-stack Progressive Web App (PWA) combining computer vision, GPT-4 intelligence, and personalized health insights.

---

## 🏗️ Architecture

This is a **monorepo** containing both backend and frontend:

```
sarma/
├── backend/          # FastAPI + PostgreSQL + OpenAI
├── pwa/             # React 18 + TypeScript PWA
└── README.md        # This file
```

---

## 🚀 Quick Start

### Backend (FastAPI)

```bash
cd backend
docker-compose up -d
# Access API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### PWA Frontend

```bash
cd pwa
npm install
npm run dev
# Access: http://localhost:3000
```

---

## 📦 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL 15** - Database with pgvector extension
- **SQLAlchemy 2.0** - ORM with async support
- **OpenAI GPT-4 Vision** - Meal analysis & recipe generation
- **Pydantic v2** - Data validation
- **Docker** - Containerization

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **React Query** - Data fetching
- **PWA** - Installable, offline-first

---

## 🌟 Features

### Core Features
- 📸 **Photo Meal Logging** - Snap photos, AI analyzes nutrition
- 🤖 **AI Chat Assistant** - GPT-4 powered health Q&A
- 🥗 **Recipe Discovery** - Personalized recommendations
- 📊 **Health Dashboard** - Track metrics, goals, progress
- 🛒 **Smart Shopping Lists** - Auto-generated from meal plans
- 💊 **Supplement Tracking** - Manage vitamins & medications

### Technical Features
- 🔐 JWT Authentication
- 📱 Progressive Web App (installable)
- 🔄 Offline support
- 📈 Vector similarity search (pgvector)
- 🎨 Responsive design (mobile-first)
- 🐳 Docker-ready

---

## 📊 Project Stats

- **96 source files**
- **20,628 lines of code**
- **46 REST API endpoints**
- **46 database tables**
- **6 PWA pages**
- **11 UI components**
- **100% TypeScript/Python**

---

## 🚀 Deploy to Railway

### Deploy Backend

```bash
cd backend
railway init
railway add  # Add PostgreSQL + Redis
railway up
```

### Deploy PWA

```bash
cd pwa
railway init
railway up
```

**Environment Variables Needed:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `DATABASE_URL` - Provided by Railway
- `REDIS_URL` - Provided by Railway
- `SECRET_KEY` - Generate with `openssl rand -hex 32`

---

## 📚 Documentation

Full documentation available in `/outputs/`:
- `🚀_START_HERE_FIRST.md` - Quick overview
- `RAILWAY_DEPLOYMENT_GUIDE.md` - Deployment instructions
- `PROJECT_STRUCTURE.txt` - Full architecture
- `PWA_QUICK_START.md` - Frontend guide

---

## 🔑 API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token

### Meals
- `POST /api/v1/meals/` - Log meal with photo
- `GET /api/v1/meals/` - List user's meals
- `GET /api/v1/meals/{id}` - Get meal details
- `DELETE /api/v1/meals/{id}` - Delete meal

### Recipes
- `GET /api/v1/recipes/` - Browse recipes
- `GET /api/v1/recipes/{id}` - Recipe details
- `POST /api/v1/recipes/generate` - AI recipe generation
- `GET /api/v1/recipes/search` - Vector similarity search

### Health
- `GET /api/v1/health/metrics` - Health dashboard
- `POST /api/v1/health/goals` - Set health goals
- `GET /api/v1/health/insights` - AI-generated insights

### Chat
- `POST /api/v1/chat/` - Send message to AI
- `GET /api/v1/chat/history` - Conversation history

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
# Current coverage: ~10%
```

### PWA Tests
```bash
cd pwa
npm test
```

---

## 💰 Cost Estimate (Railway)

- **Backend Service:** ~$10/month (1GB RAM)
- **PWA Service:** ~$5/month (Static hosting)
- **PostgreSQL:** ~$5/month (512MB)
- **Redis:** Included in backend

**Total: ~$20/month** (First month free with trial)

---

## 🛣️ Roadmap

### Phase 1: MVP (Complete ✅)
- [x] User authentication
- [x] Meal photo logging
- [x] Recipe browsing
- [x] Health dashboard
- [x] PWA frontend
- [x] Docker deployment

### Phase 2: AI Enhancement (30% Complete)
- [x] OpenAI integration setup
- [ ] GPT-4 Vision meal analysis
- [ ] AI recipe generation
- [ ] Vector similarity search
- [ ] Chat Q&A system

### Phase 3: Production (10% Complete)
- [ ] Comprehensive testing
- [ ] Payment integration
- [ ] Admin dashboard
- [ ] Analytics & monitoring
- [ ] Performance optimization

### Phase 4: Growth
- [ ] Mobile native apps
- [ ] Social features
- [ ] Partnerships API
- [ ] Viral marketing tools
- [ ] Advanced analytics

---

## 📄 License

Proprietary - All rights reserved

---

## 👨‍💻 Developer

Built with ❤️ by Darko

**Contact:** [Your email/website]

---

## 🙏 Acknowledgments

- OpenAI GPT-4 for AI capabilities
- Railway for hosting infrastructure
- React & FastAPI communities

---

**Ready to revolutionize nutrition tracking! 🚀**
