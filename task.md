# ML Funnel & Frontend Enhancements

## Database & Data Generation
- [x] Rename items in `items.csv` to use realistic dish names (e.g., "Butter Chicken", "Masala Dosa").

## Backend 4-Stage Funnel (Lightweight/Numpy/FAISS)
- [x] Stage 1: Retrieval (GraphSAGE + Siamese). Implement FAISS (HNSW) indexing using item embeddings generated via Category/Rating similarities.
- [x] Stage 2: Sequence (BERT4Rec). Implement a lightweight Attention layer (numpy) over the current `cart_items` to generate a contextual query vector predicting the next category.
- [x] Stage 3: Ranking (DLRM). Implement User & Item embeddings (mocked) and compute interaction dot products, returning probabilities mapping to Focal Loss concepts.
- [x] Stage 4: Business Logic. Keep current price anchoring (`min(50, Cart Value * 0.4)`) and meal time/packaging filters.
- [x] New Endpoint: `/api/v1/reject`. Store rejected items per `user_id` in-memory. Ensure blocked items are omitted from future recommendations.

## 1. Architecture & Infrastructure
- [/] Bring back **Redis** in `docker-compose.yml`. Use `redis-py` in the Python backend to cache frequently accessed data (e.g., top-rated items, search results).
- [/] Remove all time-of-day/clock logic from the backend recommendation pipeline and frontend.

## Frontend Updates
- [x] Display "Trending in Area (Sold in last 1 hour)" tag on top items.
- [x] Add a visible "Reject" (X) button on Recommended Items in the CSAO rail.
- [x] When "Reject" is clicked, remove the visual card instantly and send `/api/v1/reject` to the backend.

## Documentation
- [x] Update `README.md` to reflect the 4-stage funnel (with textual flow chart).
- [x] Update `implementation_plan.md` to map out these additions.
- [x] Ensure all unused files are removed.
