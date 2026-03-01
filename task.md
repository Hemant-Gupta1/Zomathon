# Project Titan: Cart Super Add-On (CSAO) Rail

## Planning & Architecture
- [x] Read dataset schema (users, items, interactions, restaurants)
- [x] Define precise directory tree structure
- [x] Write directory structure to a file / chat

## Infrastructure Setup
- [x] Generate updated docker-compose.yml (Lean Mode)
  - NGINX gateway
  - Single Redis instance
  - Single PostgreSQL instance 
  - Single MongoDB instance
  - Python AI Core service (embedded FAISS)
  - GoLang Re-Ranking service
  - Evaluation batch service

## Gateway & Feature Store
- [x] NGINX configuration (10ms budget)
- [x] Feast Feature Store configuration (15ms budget)
- [x] Feature Engineering logic (Time Cyclical, OpenWeather, Cart Composition)
  
## Python AI Core (Multi-Stage Cascade)
- [x] Stage 1: FAISS embedded retrieval with GraphSAGE & Siamese Networks
- [x] Stage 2: BERT4Rec Sequential Modeling (In-memory PyTorch)
- [x] Stage 3: DLRM Ranking (In-memory PyTorch)
- [x] Component 3 integration: YOLO v8, Swin Transformers, BERT embeddings, Llama 3 RAG
- [x] Python Main FastAPI Service routing & logic

## Business Logic Re-Ranking (GoLang)
- [x] GoLang microservice main logic (grpc server) (20ms budget)
- [x] Price Anchoring & Geohash filters
- [x] Proximity Logistics (Google Routes)
- [x] Rejection Feedback using Redis Bloom Filter

## Evaluation Framework
- [x] Evaluation scripts (AUC, NDCG@K, Precision@K, Recall@K)
