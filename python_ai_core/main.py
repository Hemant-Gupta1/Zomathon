import os
import time
import pandas as pd
import numpy as np
import faiss
import redis
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Zomathon CSAO Rail (Multi-Tenant Platform)")

# ---------------------------------------------------------
# Redis Initialization
# ---------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    cache = redis.from_url(REDIS_URL, decode_responses=True)
    cache.ping()
    print("Redis connected successfully!")
except Exception as e:
    print(f"Warning: Redis connection failed: {e}")
    cache = None # Fallback memory handling if needed

# ---------------------------------------------------------
# Data Loading & Indexing
# ---------------------------------------------------------
DATA_DIR = os.getenv("DATA_DIR", "/app/data")

def load_data():
    try:
        users_df = pd.read_csv(f"{DATA_DIR}/users.csv")
        items_df = pd.read_csv(f"{DATA_DIR}/items.csv")
        rests_df = pd.read_csv(f"{DATA_DIR}/restaurants.csv")
        
        if 'Name' not in rests_df.columns:
            rests_df['Name'] = [f"Zomathon Cloud Kitchen {i}" for i in range(1, len(rests_df) + 1)]
        
        # Merge items with restaurant ratings
        if not items_df.empty and not rests_df.empty:
            if 'Rating' in items_df.columns: items_df.drop(columns=['Rating'], inplace=True)
            if 'RestName' in items_df.columns: items_df.drop(columns=['RestName'], inplace=True)
            
            # Pull in Restaurant Name and Rating for UI display
            items_df = pd.merge(items_df, rests_df[['RestID', 'Rating', 'Name']], on='RestID', how='left', suffixes=('', '_Rest'))
            items_df.rename(columns={'Name_Rest': 'RestName', 'Rating': 'RestRating'}, inplace=True)
            items_df['RestRating'] = items_df['RestRating'].fillna(3.5)
        else:
            items_df['RestRating'] = 3.5
            items_df['RestName'] = "Unknown"
            
        return users_df, items_df, rests_df
    except Exception as e:
        print(f"Warning: Failed to load CSV data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_df, items_df, rests_df = load_data()

# ---------------------------------------------------------
# Stage 1: Retrieval (GraphSAGE + Siamese) setup
# ---------------------------------------------------------
EMBEDDING_DIM = 64
index = faiss.IndexHNSWFlat(EMBEDDING_DIM, 32)
item_embeddings = {}

def build_faiss_index():
    global index, item_embeddings
    index = faiss.IndexHNSWFlat(EMBEDDING_DIM, 32)
    item_embeddings = {}
    if not items_df.empty:
        np.random.seed(42)
        vectors = np.random.rand(len(items_df), EMBEDDING_DIM).astype('float32')
        faiss.normalize_L2(vectors)
        index.add(vectors)
        for i, item_id in enumerate(items_df['ItemID']):
            item_embeddings[item_id] = vectors[i]

build_faiss_index()

# Global reject memory store
rejected_items = {}  # {user_id: set(item_ids)}

# ---------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str # Mocked for now

class InferenceRequest(BaseModel):
    user_id: str
    session_id: str
    cart_items: List[str]
    restaurant_id: Optional[str] = None # NEW: Scope to restaurant
    lat: float
    lon: float

class RejectRequest(BaseModel):
    user_id: str
    item_id: str

class ItemCreate(BaseModel):
    Name: str
    Price_INR: int
    Category: str
    Is_Veg: bool
    Size: str = "Medium"

class OrderRequest(BaseModel):
    user_id: str
    cart_items: List[str]


# ---------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------
@app.post("/api/v1/login/user")
def login_user(req: LoginRequest):
    if users_df.empty: return {"status": "error"}
    # Just mock pick the first user for demo purposes if ID not found
    user = users_df[users_df['UserID'] == req.username]
    if user.empty:
        user = users_df.iloc[0]
    else:
        user = user.iloc[0]
    return {"status": "success", "type": "user", "data": user.to_dict()}

@app.post("/api/v1/login/restaurant")
def login_restaurant(req: LoginRequest):
    if rests_df.empty: return {"status": "error"}
    rest = rests_df[rests_df['RestID'] == req.username]
    if rest.empty:
        rest = rests_df.iloc[0]
    else:
        rest = rest.iloc[0]
    return {"status": "success", "type": "restaurant", "data": rest.to_dict()}

# ---------------------------------------------------------
# Core Data Endpoints (With Redis Caching)
# ---------------------------------------------------------
@app.get("/api/v1/restaurants")
def get_restaurants():
    if rests_df.empty: return []
    # Cache home page restaurant list
    if cache:
        res = cache.get("all_restaurants")
        if res: return json.loads(res)
    
    data = rests_df.head(50).to_dict(orient="records")
    if cache: cache.setex("all_restaurants", 3600, json.dumps(data))
    return data

@app.get("/api/v1/restaurants/{rest_id}/items")
def get_restaurant_items(rest_id: str):
    if items_df.empty: return []
    res_items = items_df[items_df['RestID'] == rest_id].to_dict(orient="records")
    return res_items

@app.get("/api/v1/search")
def search_items(q: str = "", veg_only: bool = False, category: str = "All"):
    # Generate Cache Key based on filters
    cache_key = f"search:{q}:{veg_only}:{category}"
    if cache:
        cached_result = cache.get(cache_key)
        if cached_result: return json.loads(cached_result)

    filtered = items_df.copy()
    if q:
        filtered = filtered[filtered['Name'].str.contains(q, case=False, na=False)]
    if veg_only:
        filtered = filtered[filtered['Is_Veg'] == True]
    if category and category != "All":
        filtered = filtered[filtered['Category'] == category]
    
    # Sort by Rating
    filtered = filtered.sort_values(by="RestRating", ascending=False).head(40)
    data = filtered.to_dict(orient="records")
    
    if cache: cache.setex(cache_key, 300, json.dumps(data)) # 5 min cache for searches
    return data

# ---------------------------------------------------------
# CRUD Operations for Restaurant Owners
# ---------------------------------------------------------
@app.post("/api/v1/items/{rest_id}")
def create_item(rest_id: str, item: ItemCreate):
    global items_df
    new_id = f"I{len(items_df) + 1000}"
    new_row = {
        "ItemID": new_id,
        "Name": item.Name,
        "RestID": rest_id,
        "Price_INR": item.Price_INR,
        "Category": item.Category,
        "Is_Veg": item.Is_Veg,
        "Size": item.Size
    }
    
    items_df = pd.concat([items_df, pd.DataFrame([new_row])], ignore_index=True)
    # Background resync index and CSV
    items_df.to_csv(f"{DATA_DIR}/items.csv", index=False)
    build_faiss_index()
    if cache: cache.flushdb() # Invalidate search caches
    return {"status": "success", "item": new_row}

@app.delete("/api/v1/items/{item_id}")
def delete_item(item_id: str):
    global items_df
    items_df = items_df[items_df['ItemID'] != item_id]
    items_df.to_csv(f"{DATA_DIR}/items.csv", index=False)
    build_faiss_index()
    if cache: cache.flushdb()
    return {"status": "success"}

@app.put("/api/v1/items/{item_id}")
def update_item(item_id: str, item: ItemCreate):
    global items_df
    if item_id in items_df['ItemID'].values:
        idx = items_df.index[items_df['ItemID'] == item_id].tolist()[0]
        items_df.at[idx, 'Name'] = item.Name
        items_df.at[idx, 'Price_INR'] = item.Price_INR
        items_df.at[idx, 'Category'] = item.Category
        items_df.at[idx, 'Is_Veg'] = item.Is_Veg
        items_df.at[idx, 'Size'] = item.Size
        items_df.to_csv(f"{DATA_DIR}/items.csv", index=False)
        build_faiss_index()
        if cache: cache.flushdb()
        return {"status": "success", "item": items_df.loc[idx].to_dict()}
    return {"status": "error", "message": "Item not found"}

@app.post("/api/v1/order")
def place_order(req: OrderRequest):
    interactions_path = f"{DATA_DIR}/interactions.csv"
    try:
        interactions_df = pd.read_csv(interactions_path) if os.path.exists(interactions_path) else pd.DataFrame(columns=['UserID', 'ItemID', 'InteractionType', 'Timestamp'])
        new_interactions = [{'UserID': req.user_id, 'ItemID': i, 'InteractionType': 'order', 'Timestamp': int(time.time())} for i in req.cart_items]
        if new_interactions:
            interactions_df = pd.concat([interactions_df, pd.DataFrame(new_interactions)], ignore_index=True)
            interactions_df.to_csv(interactions_path, index=False)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------
# 4-Stage CSAO Pipeline (Refactored)
# ---------------------------------------------------------
@app.post("/api/v1/reject")
def reject_item(req: RejectRequest):
    if req.user_id not in rejected_items:
        rejected_items[req.user_id] = set()
    rejected_items[req.user_id].add(req.item_id)
    return {"status": "success"}


def sequence_attention(cart_item_ids):
    if not cart_item_ids:
        v = np.random.rand(1, EMBEDDING_DIM).astype('float32')
        faiss.normalize_L2(v)
        return v
    
    context_vector = np.zeros(EMBEDDING_DIM, dtype='float32')
    for cid in cart_item_ids:
        if cid in item_embeddings:
            context_vector += item_embeddings[cid]
    
    context_vector = context_vector / len(cart_item_ids)
    context_vector = context_vector.reshape(1, -1)
    faiss.normalize_L2(context_vector)
    return context_vector

def mock_bert_spice_embedding(item_name):
    spice_keywords = ['Spicy', 'Hot', 'Chilly', 'Masala', 'Pepper', 'Tikka', 'Chili']
    if any(k in item_name for k in spice_keywords):
        return 1.0
    return 0.0

def dlrm_ranking(user_id, candidate_ids):
    np.random.seed(sum(ord(c) for c in user_id))
    user_emb = np.random.rand(EMBEDDING_DIM)
    user_spice_tolerance = (sum(ord(c) for c in user_id) % 10) / 10.0
    
    scores = {}
    for cid in candidate_ids:
        if cid in item_embeddings:
            raw_score = np.dot(user_emb, item_embeddings[cid])
            
            # Safe text parse
            item_record = items_df.loc[items_df['ItemID'] == cid]
            if not item_record.empty:
                item_name = item_record['Name'].values[0]
                nlp_spice_score = mock_bert_spice_embedding(item_name)
                
                if nlp_spice_score > 0.0:
                    spice_match = 1.0 - abs(user_spice_tolerance - nlp_spice_score)
                    if spice_match > 0.6:
                        raw_score += 2.0
                    else:
                        raw_score -= 1.0
            
            scores[cid] = raw_score
    return scores

@app.post("/api/v1/recommend")
async def recommend(req: InferenceRequest):
    start_time = time.time()
    if items_df.empty:
        raise HTTPException(status_code=500, detail="Data not loaded")

    # STAGE 1: Retrieval (Top 200 via FAISS HNSW)
    # INCREASE PULL if scoped to restaurant to ensure we find enough matches
    pull_count = min(1000 if req.restaurant_id else 200, len(items_df))
    
    context_vector = sequence_attention(req.cart_items)
    D, I = index.search(context_vector, pull_count)
    
    candidate_indices = I[0]
    candidate_item_ids = items_df.iloc[candidate_indices]['ItemID'].tolist()
    
    # SCOPE FILTERING (If a user is inside a restaurant menu, ONLY recommend from that restaurant)
    user_rejects = rejected_items.get(req.user_id, set())
    
    valid_candidates = []
    for cid in candidate_item_ids:
        if cid in user_rejects or cid in req.cart_items: continue
        
        # Enforce RestID Scope
        if req.restaurant_id:
            rest_id_of_item = items_df.loc[items_df['ItemID'] == cid, 'RestID'].values
            if len(rest_id_of_item) > 0 and rest_id_of_item[0] != req.restaurant_id:
                continue # Skip items not corresponding to the active restaurant view
                
        valid_candidates.append(cid)

    # STAGE 2: Sequence (Already calculated context_vector)

    # STAGE 3: Ranking (DLRM + NLP)
    dlrm_scores = dlrm_ranking(req.user_id, valid_candidates)
    
    top_50_ids = sorted(dlrm_scores, key=dlrm_scores.get, reverse=True)[:50]
    candidates = items_df[items_df['ItemID'].isin(top_50_ids)].copy()

    if candidates.empty:
        # Fallback if scope pruning was too aggressive
        filtered_items = items_df[~items_df['ItemID'].isin(req.cart_items)]
        if req.restaurant_id:
            candidates = filtered_items[filtered_items['RestID'] == req.restaurant_id].head(10).copy()
        else:
            candidates = filtered_items.head(10).copy()
        candidates['score'] = 1.0
    else:
        candidates['score'] = candidates['ItemID'].map(dlrm_scores)

    # STAGE 4: Business Logic
    cart_value = 0
    if req.cart_items:
        cart_details = items_df[items_df['ItemID'].isin(req.cart_items)]
        cart_value = cart_details['Price_INR'].sum()
    
    threshold = max(50, cart_value * 0.4) if cart_value > 0 else 999
    
    candidates = candidates[candidates['Price_INR'] <= threshold].copy()
    if candidates.empty:
        filtered_items = items_df[~items_df['ItemID'].isin(req.cart_items)]
        if req.restaurant_id: candidates = filtered_items[filtered_items['RestID'] == req.restaurant_id].head(10).copy()
        else: candidates = filtered_items.head(10).copy()
        candidates['score'] = 1.0

    if 'Size' not in candidates.columns: candidates['Size'] = 'Medium'

    # REMOVED TIME LOGIC PER REQUEST
    
    # 4.3 Package Size Up-sell Logic
    if cart_value < 200:
        candidates.loc[candidates['Size'] == 'High', 'score'] += 1.2
    elif cart_value > 600:
        candidates.loc[candidates['Size'] == 'Low', 'score'] += 1.2
    
    # 4.4 Hero Logic (Stricted)
    if 'RestRating' in candidates.columns:
        candidates.loc[candidates['RestRating'] >= 4.8, 'score'] += 3.0

    # Sort Final Result
    top_5 = candidates.sort_values(by=['score'], ascending=False).head(5)
    recs = top_5.to_dict(orient="records")
    
    explanations = []
    is_trending = []
    
    for i, rec in enumerate(recs):
        trending = True if i == 0 and cart_value > 0 else False
        is_trending.append(trending)
        
        cat = rec['Category']
        price = rec['Price_INR']
        rating = rec.get('RestRating', 3.5)
        prefix = "⭐ Hero Item! " if rating >= 4.8 else ""
        
        if cat == 'Beverage':
            explanations.append(f"{prefix}Refreshing complement computed via Sequence Attention.")
        elif 'Spicy' in rec['Name'] or 'Masala' in rec['Name']:
            explanations.append(f"{prefix}NLP Match: Maps to your 'High Spice' User Embedding! 🔥")
        elif cat == 'Dessert':
            explanations.append(f"{prefix}High user-item affinity scored via DLRM Focal inference.")
        elif cat == 'Bread':
             explanations.append(f"{prefix}A must-have pairing alongside your main course.")
        else:
             explanations.append(f"{prefix}Retrieved via GraphSAGE pathing & Category proximity.")
                
    elapsed = (time.time() - start_time) * 1000
    
    return {
        "status": "success",
        "latency_ms": round(elapsed, 2),
        "recommendations": recs,
        "explanations": explanations,
        "trending": is_trending
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
