# Project Titan: Cart Super Add-On (CSAO) Rail (Lean Local Dev Mode)

## E2E Intelligent Recommendation System Architecture
This repository contains the architecture and scaffolding for the Project Titan CSAO Rail, which aims to maximize the conditional probability of acceptance for recommended meal add-ons under a strict 200ms budget limit.

### ⚠️ Lightweight Local Dev Mode
This system has been modified from full production specifications to run on strictly limited local dev hardware.
- **Triton Inference Server** has been dropped. PyTorch models (DLRM/BERT4Rec) run locally in-memory within the Python FastAPI process.
- **Milvus Vector DB** has been dropped. It is replaced by an embedded in-memory FAISS HNSW instance inside the Python core.
- **Postgres Replicas** have been dropped. A single Master PostgreSQL instance is used.

## Architecture Structure
The project is split into the following containerized sub-components:
- **`gateway/`**: NGINX Load Balancer routing to core microservices (10ms budget). Single MongoDB container runs adjacent to this for general metadata.
- **`feature_store/`**: Feast implementation backed by a single Redis & Postgres DB containing feature logic like Time-Cyclical encoding (15ms budget).
- **`python_ai_core/`**: The FastAPI central brain connecting the 4-stage cascade (115ms budget total). 
  - Stage 1: GraphSAGE & Embedded FAISS HNSW retrieval
  - Stage 2: BERT4Rec sequential modeling (local PyTorch)
  - Stage 3: DLRM via local PyTorch inference
  - Component 3: Multimodal CV extracts and Llama 3 gen-AI explanations.
- **`golang_rerank/`**: Business logic rules engine (20ms budget) handling price anchoring and geography restrictions.
- **`evaluation/`**: Scripts to measure NDCG@K, AUC, and business metrics.

## How to Run
The entire application is orchestrated using Docker Compose. Before you run this, you can purge old containers using commands like `docker system prune -a --volumes` to free disk space if needed.

1. **Start the Infrastructure**
   This spins up NGINX, Redis, PostgreSQL, Mongo, and the custom Python & Go services.
   ```bash
   cd c:\Zomathon\Zomathon
   docker-compose up -d --build
   ```

2. **Verify Containers are Running**
   Ensure all services report as "Up".
   ```bash
   docker-compose ps
   ```

## How to Test

### 1. Test the Gateway & Core Pipeline
You can test the entire E2E cascade by sending a payload through the NGINX gateway. This payload represents a cart checkout attempt:

**cURL Command:**
```bash
curl -X POST http://localhost:80/api/v1/recommend \
     -H "Content-Type: application/json" \
     -d '{
           "user_id": "U0015",
           "session_id": "S12345",
           "cart_items": ["I0100", "I0250"],
           "lat": 28.5,
           "lon": 77.2
         }'
```

**Expected Return:**
You should see a generated JSON response containing the fallback / recommended Top 5 items, the circuit breaker latency metric, and the GenAI meal completion explanation.

### 2. Run the Evaluation Framework
To run the automated AUC and business metrics evaluator:

```bash
cd c:\Zomathon\Zomathon\evaluation
pip install -r requirements.txt
python evaluate.py
```