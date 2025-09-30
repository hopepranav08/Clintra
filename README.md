# Clintra - AI-Powered Drug Discovery Assistant

Clintra is a **startup-level** AI-powered drug discovery platform that helps researchers search biomedical literature, generate hypotheses, and download compound data using cutting-edge AI technologies. Built for hackathons and production deployment.

## 🚀 **Startup-Level Features**

### **Professional UI/UX**
- **ChatGPT-like Interface**: Dark theme with professional typography
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Feedback**: Loading states, error handling, offline detection
- **User Experience**: Smooth animations, intuitive navigation

### **Enterprise-Grade Security**
- **JWT Authentication**: Secure user sessions with token expiration
- **Rate Limiting**: 30 requests per minute per IP address
- **Input Validation**: Query length limits and sanitization
- **Password Security**: bcrypt hashing with salt
- **CORS Protection**: Restricted origins and trusted hosts

### **Production-Ready Architecture**
- **Microservices**: Docker MCP Gateway pattern
- **Database**: PostgreSQL with proper schema design
- **Error Handling**: Comprehensive error responses and logging
- **Performance**: Request timeouts, caching, optimization
- **Monitoring**: Health checks and status endpoints

### **AI Integration**
- **Cerebras AI**: High-performance inference for hypothesis generation
- **Llama Embeddings**: Semantic search and Q&A capabilities
- **Pinecone**: Vector database for similarity search
- **RAG Pipeline**: Retrieval-Augmented Generation for accurate responses

## 🎯 **Core Features**

### **1. Literature Search**
- **PubMed Integration**: Real-time article search with working links
- **Clinical Trials**: ClinicalTrials.gov integration
- **AI Summary**: Intelligent summarization of results
- **Citations**: Clickable references and DOI links

### **2. Hypothesis Generation**
- **AI-Powered**: Cerebras inference for research hypotheses
- **Context-Aware**: Uses literature and compound data
- **Plausibility Scoring**: Confidence metrics for hypotheses
- **Supporting Evidence**: Citations and references

### **3. Data Download**
- **PubChem Integration**: Compound information and structures
- **PDB Integration**: Protein structure data
- **Multiple Formats**: JSON, SDF, PDB, CIF formats
- **3D Visualization**: Interactive structure viewers

### **4. Graph Visualization**
- **Network Analysis**: Relationship mapping
- **Interactive Graphs**: Zoom, pan, and explore
- **Download Options**: PNG, SVG, JSON formats
- **Custom Layouts**: Multiple visualization types

### **5. User Management**
- **Authentication**: Secure registration and login
- **Chat History**: Persistent conversation storage
- **Session Management**: Multiple chat sessions
- **User Profiles**: Personal information and preferences

## 🛠 **Technology Stack**

### **Backend**
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM with relationships
- **PostgreSQL**: Production-ready database
- **JWT**: Secure authentication tokens
- **Docker**: Containerized deployment

### **Frontend**
- **React 18**: Modern React with hooks
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client with interceptors
- **Local Storage**: Client-side session management

### **AI/ML**
- **Cerebras**: High-performance AI inference
- **Llama**: Language model embeddings
- **Pinecone**: Vector database for search
- **RAG**: Retrieval-Augmented Generation

### **Infrastructure**
- **Docker Compose**: Multi-service orchestration
- **Nginx**: Reverse proxy and load balancing
- **PostgreSQL**: Relational database
- **Redis**: Caching and session storage

## 🚀 **Quick Start**

### **Prerequisites**
- Docker and Docker Compose
- Git
- Modern web browser

### **1. Clone and Setup**
```bash
git clone <repository-url>
cd clintra
cp .env.example .env
```

### **2. Start Services**
```bash
docker compose up --build -d
```

### **3. Access Application**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### **4. Test Features**
1. Register a new account
2. Try all four modes (Literature, Hypothesis, Download, Graph)
3. Test chat history and persistence
4. Verify offline/online functionality
5. Check rate limiting and error handling

## 📁 **Project Structure**

```
clintra/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api.py             # Main API endpoints
│   │   ├── auth.py            # Authentication & security
│   │   ├── models.py          # Database models
│   │   ├── rag.py             # RAG pipeline
│   │   ├── graph.py           # Graph generation
│   │   ├── deps.py            # Dependencies
│   │   └── connectors/        # External API connectors
│   │       ├── pubmed.py      # PubMed integration
│   │       ├── pubchem.py     # PubChem integration
│   │       ├── pdb.py         # PDB integration
│   │       └── trials.py      # Clinical trials
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend container
├── frontend/                  # React frontend
│   ├── app/
│   │   ├── src/
│   │   │   ├── App.jsx        # Main React component
│   │   │   ├── components/    # React components
│   │   │   └── index.css      # Global styles
│   │   ├── package.json       # Node dependencies
│   │   └── Dockerfile        # Frontend container
├── db/                        # Database schema
│   └── schema.sql            # SQL schema
├── docker-compose.yml         # Service orchestration
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🔌 **API Endpoints**

### **Authentication**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user info

### **Core Features**
- `POST /api/search` - Search literature (PubMed + Clinical Trials + RAG)
- `POST /api/hypothesis` - Generate AI hypothesis
- `POST /api/download` - Download compound/protein data
- `POST /api/graph` - Generate network visualization

### **Chat Management**
- `GET /api/chat/sessions` - Get user's chat sessions
- `POST /api/chat/sessions` - Create new chat session
- `GET /api/chat/sessions/{id}/messages` - Get session messages
- `POST /api/chat/sessions/{id}/messages` - Add message to session

### **System**
- `GET /api/health` - Health check
- `GET /api/debug-env` - Environment debugging

## ⚙️ **Configuration**

### **Environment Variables**
```env
# Database
POSTGRES_USER=clintra
POSTGRES_PASSWORD=clintra123
POSTGRES_DB=clintra

# AI Services
PINECONE_API_KEY=your_pinecone_key
CEREBRAS_API_KEY=your_cerebras_key
CEREBRAS_API_URL=your_cerebras_url

# Security
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### **Rate Limiting**
- **Default**: 30 requests per minute per IP
- **Configurable**: Modify `rate_limit_middleware`
- **Error Response**: 429 Too Many Requests

### **Request Timeouts**
- **External APIs**: 10 seconds
- **Database Queries**: 5 seconds
- **Error Handling**: Graceful degradation

## 🧪 **Testing**

### **Automated Tests**
```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend/app
npm test
```

### **Manual Testing Checklist**
- [ ] User registration and login
- [ ] All four modes (Literature, Hypothesis, Download, Graph)
- [ ] Chat history persistence
- [ ] Offline/online detection
- [ ] Rate limiting (30 requests/minute)
- [ ] Error handling and recovery
- [ ] Link functionality (PubMed, Clinical Trials, PubChem, PDB)
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Performance under load
- [ ] Security (authentication, authorization)

## 🔒 **Security Features**

### **Authentication & Authorization**
- JWT tokens with expiration
- bcrypt password hashing
- Session management
- User role-based access

### **Input Validation**
- Query length limits (500 characters)
- SQL injection prevention
- XSS protection
- CSRF protection

### **Rate Limiting**
- IP-based rate limiting
- Configurable limits
- Graceful error responses
- Request logging

### **Network Security**
- CORS protection
- Trusted host middleware
- HTTPS enforcement (production)
- Security headers

## 📊 **Performance Features**

### **Optimization**
- Database connection pooling
- Query optimization
- Response caching
- Lazy loading

### **Monitoring**
- Health check endpoints
- Performance metrics
- Error tracking
- Request logging

### **Scalability**
- Horizontal scaling support
- Load balancing ready
- Database sharding support
- Microservices architecture

## 🚀 **Deployment**

### **Development**
```bash
docker compose up --build
```

### **Production**
```bash
# Set production environment variables
export NODE_ENV=production
export DATABASE_URL=postgresql://user:pass@host:port/db

# Build and deploy
docker compose -f docker-compose.prod.yml up -d
```

### **Cloud Deployment**
- **AWS**: ECS, RDS, CloudFront
- **Google Cloud**: Cloud Run, Cloud SQL, CDN
- **Azure**: Container Instances, Database, CDN
- **DigitalOcean**: App Platform, Managed Database

## 📈 **Monitoring & Analytics**

### **Health Checks**
- Backend: `GET /api/health`
- Database: Connection monitoring
- External APIs: Timeout handling
- Frontend: Error boundary

### **Logging**
- Application logs
- Error tracking
- Performance metrics
- User activity

### **Analytics**
- User engagement
- Feature usage
- Performance metrics
- Error rates

## 🤝 **Contributing**

### **Development Workflow**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### **Code Standards**
- Python: PEP 8, type hints
- JavaScript: ESLint, Prettier
- Git: Conventional commits
- Documentation: Inline comments

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 **Support**

### **Getting Help**
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Comprehensive guides and API docs
- **Community**: Discord/Slack channels
- **Email**: support@clintra.com

### **Troubleshooting**
- Check Docker logs: `docker compose logs`
- Verify environment variables
- Test API endpoints: `curl http://localhost:8000/api/health`
- Check browser console for errors

## 🗺️ **Roadmap**

### **Phase 1: Core Features** ✅
- [x] User authentication
- [x] Literature search
- [x] Hypothesis generation
- [x] Data download
- [x] Graph visualization
- [x] Chat history

### **Phase 2: Advanced Features** 🚧
- [ ] Advanced graph visualizations
- [ ] Team collaboration
- [ ] API rate limiting per user
- [ ] Advanced search filters
- [ ] Export functionality
- [ ] Real-time notifications

### **Phase 3: Scale & Integrate** 📋
- [ ] Mobile app
- [ ] More database integrations
- [ ] Advanced analytics
- [ ] Multi-language support
- [ ] Enterprise features
- [ ] API marketplace

## 🏆 **Hackathon Ready**

This project is **hackathon-ready** with:
- ✅ Complete functionality
- ✅ Professional UI/UX
- ✅ Working features
- ✅ User authentication
- ✅ Chat history
- ✅ Real citations and links
- ✅ Startup-level quality
- ✅ Production deployment ready

**Perfect for**: AI/ML hackathons, drug discovery competitions, startup pitches, and production deployment.

---

**Built with ❤️ for the drug discovery community**