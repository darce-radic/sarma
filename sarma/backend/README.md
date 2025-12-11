# 🚀 Forecast Health - Backend API

AI-Powered Metabolic Health + Smart Shopping Platform

---

## 🏗️ **Architecture**

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+ with pgvector
- **ORM**: SQLAlchemy 2.0 (async)
- **Authentication**: JWT tokens
- **AI**: OpenAI API (GPT-4, GPT-4 Vision, Embeddings)
- **Cache**: Redis
- **Testing**: Pytest + httpx

---

## 🚀 **Quick Start**

### **Option 1: Docker (Recommended)**

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# API available at: http://localhost:8000
```

### **Option 2: Local Development**

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database (PostgreSQL must be running)
createdb forecast_db

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload

# API available at: http://localhost:8000
```

---

## 📚 **API Documentation**

Once the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/v1/health

---

## 🧪 **Testing**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_auth.py -v

# Open coverage report
open htmlcov/index.html
```

---

## 🔑 **API Endpoints (Available Now)**

### **Authentication**
- `POST /v1/auth/register` - Register new user
- `POST /v1/auth/login` - User login
- `POST /v1/auth/refresh` - Refresh access token

### **Users**
- `GET /v1/users/me` - Get current user profile
- `PATCH /v1/users/me` - Update user profile
- `PATCH /v1/users/me/health-profile` - Update health profile
- `PATCH /v1/users/me/preferences` - Update preferences

---

## 📁 **Project Structure**

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py          ✅ Implemented
│   │       │   └── users.py         ✅ Implemented
│   │       └── api.py
│   ├── core/
│   │   ├── config.py                ✅ Configuration
│   │   ├── database.py              ✅ Database connection
│   │   └── security.py              ✅ JWT & password hashing
│   ├── models/
│   │   └── user.py                  ✅ User models
│   ├── schemas/
│   │   └── user.py                  ✅ Pydantic schemas
│   └── main.py                      ✅ FastAPI app
├── tests/
│   └── test_auth.py                 ✅ Authentication tests
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

---

## 🔐 **Environment Variables**

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/forecast_db

# Authentication
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# OpenAI
OPENAI_API_KEY=sk-proj-your-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:19006
```

---

## 🎯 **What's Built**

✅ **Core Infrastructure**
- FastAPI application setup
- PostgreSQL with pgvector
- Redis caching
- Docker containerization
- Logging & monitoring
- CORS configuration

✅ **Authentication System**
- User registration
- Login with JWT tokens
- Token refresh
- Password hashing (bcrypt)
- Protected endpoints

✅ **User Management**
- User CRUD operations
- Health profile management
- Preferences management
- Profile updates

✅ **Database Models**
- User model
- UserHealthProfile model
- UserPreferences model
- SQLAlchemy relationships

---

## 📝 **Next Steps**

To continue building:

1. **Add Health Assessment** (`app/api/v1/endpoints/health.py`)
2. **Add Recipe Search** (`app/api/v1/endpoints/recipes.py`)
3. **Add Meal Analysis** (`app/api/v1/endpoints/meals.py`)
4. **Add OpenAI Integration** (`app/services/openai_service.py`)
5. **Add Vector Search** (`app/services/vector_search_service.py`)

---

## 🐛 **Troubleshooting**

### Database Connection Error
```bash
# Check if PostgreSQL is running
pg_isready

# Restart PostgreSQL
docker-compose restart postgres
```

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📞 **Support**

- **Issues**: Open a GitHub issue
- **Email**: dev-support@forecasthealth.app
- **Slack**: #forecast-dev

---

**Built with ❤️ by the Forecast Health team**
