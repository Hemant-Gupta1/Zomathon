# Project Titan: Cart Super Add-On (CSAO) Rail Implementation Plan

## Goal Description
Build an End-to-End Intelligent Recommendation Architecture targeting sub-200ms latency to maximize conditional probability of acceptance for recommended add-ons. The system involves an NGINX Gateway, Faust/Redis Feature Store, PyTorch/Triton AI Core for a 4-Stage Cascade (GraphSAGE, BERT4Rec, DLRM, Vision/GenAI), and a GoLang Re-Ranking engine.

## Directory Structure
```
c:\Zomathon\Zomathon\
├── docker-compose.yml
├── .env
├── gateway/
│   ├── Dockerfile
│   └── nginx.conf
├── feature_store/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── init_feast.py
│   └── feature_repo/
│       ├── feature_store.yaml
│       └── features.py
├── python_ai_core/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py (FastAPI gateway for core cascade)
│   └── cascade/
│       ├── __init__.py
│       ├── stage1_retrieval.py (Milvus, GraphSAGE, Siamese)
│       ├── stage2_sequential.py (BERT4Rec)
│       ├── stage3_ranking.py (DLRM Triton client)
│       └── component3_multimodal.py (YOLOv8, Swin, BERT, Llama3 RAG)
├── golang_rerank/
│   ├── Dockerfile
│   ├── go.mod
│   ├── main.go (gRPC Server)
│   └── rules/
│       ├── anchoring.go
│       ├── geospatial.go
│       └── feedback.go
└── evaluation/
    ├── requirements.txt
    └── evaluate.py
```

## Proposed Changes
### Root Configurations
#### [NEW] docker-compose.yml
Orchestrates:
- `gateway` (NGINX Load Balancer)
- `redis-cluster`
- `postgres-primary` & `postgres-replica`
- `milvus-standalone`, `etcd`, `minio`
- `triton-server`
- `python-ai-core`
- `golang-rerank`

### Gateway & Feature Store (10ms + 15ms Budget)
#### [NEW] gateway/nginx.conf
Configures upstream load balancing to the Python AI Core and sets strict proxy timeouts to maintain the 10ms budget.
#### [NEW] feature_store/feature_repo/feature_store.yaml & features.py
Configures Feast with Redis online store and PostgreSQL offline store. Includes logic for Time Cyclical Encoding and Cart Composition scoring.

### AI Core Microservice (Python/PyTorch - 35ms + 80ms Budget)
#### [NEW] python_ai_core/main.py
FastAPI application to act as the central orchestrator. Uses gRPC to communicate with the GoLang Re-Ranker. Implements the circuit breaker falling back to Redis if latency > 250ms.
#### [NEW] python_ai_core/cascade/stage1_retrieval.py
Outlines Milvus HNSW indexing, GraphSAGE implementation, and Siamese Triplet loss structures.
#### [NEW] python_ai_core/cascade/stage2_sequential.py
BERT4Rec implementation with Self-Attention.
#### [NEW] python_ai_core/cascade/stage3_ranking.py
DLRM Ranking with Focal loss setup and Triton Server inference calls.
#### [NEW] python_ai_core/cascade/component3_multimodal.py
Stubs for YOLOv8, Swin Transformers, and Llama 3 QLoRA integration.

### Business Logic Re-Ranking (GoLang - 20ms Budget)
#### [NEW] golang_rerank/main.go & child files
GoLang gRPC service exposing the re-ranking logic. Implements Price Anchoring, Geohash filtering, Google Routes proximity (<500m), and a 7-day Redis Bloom Filter block-list.

### Evaluation Framework
#### [NEW] evaluation/evaluate.py
Python script calculating AUC, NDCG@K, Precision@K, Recall@K, AOV Lift, and Cart-to-Order Ratio.
