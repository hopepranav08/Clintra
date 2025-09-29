# Clintra - AI-Powered Drug Discovery Assistant

Clintra is a one-stop AI platform for biomedical researchers and students, designed to accelerate drug discovery by integrating diverse biomedical data sources and providing advanced AI-powered features.

## 🚀 Key Features
- **PubMed/EuropePMC Connector**: Fetch and search research papers.
- **Drug & Compound Metadata**: Integration with DrugBank and PubChem.
- **Protein Structures**: Access to RCSB PDB data.
- **Clinical Trial Data**: Connectivity to ClinicalTrials.gov.
- **AI Hypothesis Generator**: Proposes new, testable hypotheses using advanced AI models.
- **Vector Search & Q&A**: Semantic search over ingested data powered by **Llama** models.
- **Scalable Inference**: Accelerated by **Cerebras**.
- **Modular Deployment**: Containerized with **Docker MCP Gateway**.

## 🏗 Tech Stack
- **Backend**: FastAPI, SQLAlchemy, Psycopg2, LangChain
- **Database**: PostgreSQL
- **Vector DB**: Pinecone
- **Frontend**: React, Vite, Tailwind CSS
- **Infrastructure**: Docker, Docker Compose

##  Sponsor Technologies
This project proudly integrates the following sponsor technologies:
- **Cerebras**: For high-performance, scalable AI model inference.
- **Llama**: For state-of-the-art language model capabilities in Q&A and summarization.
- **Docker MCP Gateway**: For modular, secure, and scalable containerized deployment.

## ⚙️ Setup and Installation

### Prerequisites
- Docker
- Docker Compose
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ai-drug-discovery-assistant.git
cd ai-drug-discovery-assistant
```

### 2. Configure Environment Variables
Create a `.env` file by copying the example file:
```bash
cp .env.example .env
```
Now, open the `.env` file and add your specific credentials for the following:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `PINECONE_API_KEY`
- `CEREBRAS_API_URL`

### 3. Build and Run the Application
Use Docker Compose to build and run all the services:
```bash
docker-compose up --build
```
The application will be available at the following URLs:
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000/docs`

## 🕹️ How to Use
1.  **Open the Frontend**: Navigate to `http://localhost:3000` in your web browser.
2.  **Health Check**: Click the "Check Health" button to verify that the frontend is successfully connected to the backend and the database.
3.  **Search for Papers**: Use the search bar to query PubMed for articles on a specific topic.
4.  **Generate Hypotheses**: Enter a disease, protein, or compound into the text area and click "Generate Hypothesis" to receive an AI-generated suggestion for further research.

## 📄 License
This project is licensed under the MIT License. See the `LICENSE` file for more details.