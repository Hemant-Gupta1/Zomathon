# Project Titan: CSAO Rail Full-Stack Implementation Plan (Ultra-Lightweight Mode)

## Goal Description
Build a fully functional and beautiful front-end for the Cart Super Add-On (CSAO) recommendation system and drastically simplify the backend to be as light and fast as possible. The backend uses a 4-Stage simulated ML Funnel (GraphSAGE, BERT4Rec, DLRM) built entirely in Numpy and FAISS to achieve <200ms latency without deep learning GPU overhead.

## Proposed Changes

### Configuration
#### [MODIFY] docker-compose.yml
- Keep ONLY `gateway` (NGINX) and `python-ai-core` (FastAPI). All heavy microservices removed.

### Gateway & Frontend
#### [MODIFY] gateway/nginx.conf
- Update NGINX to serve static HTML/JS/CSS frontend files directly, and proxy API requests to `python-ai-core`.
#### [MODIFY] gateway/html/
- Frontend natively displays a Glassmorphic UI, a live clock, dynamic sizing and real-time cart handling.
- Implements Reject Recommendation functionality (`/api/v1/reject`).

### AI Core Microservice (Python)
#### [MODIFY] python_ai_core/main.py
- Load CSVs directly into Pandas. Expose `/api/v1/users`, `/api/v1/items`, `/api/v1/recommend`, and `/api/v1/reject` endpoints.
#### Stage 1: Retrieval (GraphSAGE + Siamese)
- Pre-compute item embeddings (based on simulated Graph paths and Siamese category-matching combinations) on startup. Load into Faiss HNSW index.
- Given a cart item, retrieve top 200 Fast nearest neighbors.
#### Stage 2: Sequence (BERT4Rec)
- Implement a scaled dot-product attention function computing context vector across `cart_items` to predict the next compatible item embedding.
#### Stage 3: Ranking (DLRM & NLP)
- Compute dot product between User (ID+Demographics) and Item (Visual+ID) mock vectors. Map outputs using simulated probabilities mimicking Focal Loss behavior (focusing on rare cross-additions).
- **NLP Text Integration**: Simulates a BERT extraction on item names. If "Spicy" or "Masala" is detected, cross-references with a generated user "Spice Tolerance" metric to boost or penalize the DLRM score.
#### Stage 4: Business Logic
- Filter the top 50 ranked items forcing Price Anchoring <= 40% cart value.
- Track meal timings (Breakfast/Lunch/Dinner) and Cart Sizes (Small/High package).
- Store user rejected items to omit them from future outputs.
- Append tags like "Trending in area" to popular candidates.

### Documentation & Cleanup
- Update instructions for how to run `docker-compose up` and view the live website. All unused files (`feature_store`, `golang_rerank`, `pdf`s) were deleted to achieve an ultra-light workspace.
