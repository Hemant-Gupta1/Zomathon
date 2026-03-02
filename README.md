# Zomathon: Multi-Tenant Platform & Intelligent CSAO Rail

Welcome to Zomathon's core engine! 🚀

Zomathon is an ultra-fast, multi-tenant digital food delivery platform equipped with a powerful Cart Super Add-On (CSAO) Recommendation AI. We stripped away heavy machine learning frameworks like PyTorch and completely rebuilt the intelligence layer using lightning-fast mathematical representations powered by **FAISS** and **NumPy**. The result? Intelligent cross-selling pairings delivered under 200 milliseconds.

---

## 🏗️ 1. Architecture Overview

### Single-Command Deployment
The application is governed entirely by `docker-compose.yml`, which orchestrates a pristine 3-tier architecture connected securely via a custom bridge network (`titan-net`):

1. **Frontend Gateway (`nginx:alpine`)**: Runs on port `80`. Serves lightweight frontend HTML, CSS, and JS files natively and acts as a reverse proxy, instantly routing `/api/v1/*` requests back to the AI Core.
2. **AI & Logic Core (`python:3.11-slim`)**: Runs on port `8080`. The beating heart of the platform. Built using **FastAPI** and **Uvicorn**, it loads the entire restaurant catalog into **Pandas Dataframes** in RAM for instantaneous CRUD operations, eliminating database latency.
3. **High-Speed Cache (`redis:alpine`)**: Runs natively inside the cluster. Used to instantly return cached Restaurant lists and Search Results to the UI.

---

## 💻 2. Tech Stack & Dependencies

We rely on a hyper-efficient, stripped-down set of tools:

### Frontend
*   **Vanilla HTML5 & CSS3**: Pure, frameworkless UI guaranteeing zero bundle bloat and sub-second First Contentful Paint.
*   **Vanilla JavaScript (ES6+)**: Stateful logic (`app.js`) handling view routing, local storage sessions, modal toggling, Cart management, and debounced API calls for searches.
*   **FontAwesome**: Integrated via CDN for rich iconography.

### Backend Routing & Caching
*   **NGINX**: Used as an edge web server inside the `./gateway` container. We mapped `nginx.conf` to statically serve the UI and transparently `proxy_pass` to the backend.
*   **Redis**: Integrated into the Docker cluster. The Python backend connects to it utilizing the `redis` python package. We cache heavy search queries (`/search?q=x`) and global home requests for up to 5 minutes to reduce Panda computations.

### AI Core & Data Manipulation (Python)
*   **FastAPI & Uvicorn**: Chosen for extreme ASGI speed and native asynchronous handling of overlapping user connections.
*   **Pydantic**: Provides stringent type-checking for incoming REST payload models (e.g., `OrderRequest`, `ItemCreate`, `InferenceRequest`).
*   **Pandas (Data Layer)**: The entire database acts in memory via Dataframes. CRUD requests physically modify the Dataframes and instantly write via `.to_csv()` to disk asynchronously for persistence.
*   **NumPy**: Executes the matrix permutations, sequence averaging, dot-product calculations, and randomization vectors for our simulated Deep Learning mechanisms.
*   **FAISS-CPU (Facebook AI Similarity Search)**: Subsets the millions of mock vector permutations instantly. We build an `IndexHNSWFlat` index, which scales to millions of item embeddings natively in memory without requiring a GPU.

---

## 🧠 3. End-to-End ML Recommendation Flow (CSAO Rail)

The "Cart Super Add-On" (CSAO) logic lives inside `main.py` -> `/api/v1/recommend`. It is designed to act identical to a massive industrial recommendation track, simplified into 4 blistering-fast mathematical stages natively written in Python:

### **Stage 1: Scaled Retrieval (FAISS HNSW + Simulated GraphSAGE)**
When a user adds an item to their cart, we immediately convert their *active cart item identifiers* into an average Context Vector using Sequence Attention logic.
1. We query the `faiss.IndexHNSWFlat` using this vector.
2. FAISS performs an Approximate Nearest Neighbor algorithm, returning up to 1000 mathematically similar candidates based on 64-dimensional embeddings (simulating GraphSAGE edge proximities).
3. **Hard Bounds Scope Filtering**: The AI immediately strips away any item that is *already inside the user's cart* or *belongs to a different Restaurant* than the one they are currently viewing.

### **Stage 2: Sequence Inference (BERT4Rec Simulation)**
The mathematical context bridge! We simulate Transformer logic by dynamically taking the NumPy representations of everything inside the user's cart, and computing a scaled mean `context_vector`. This forces the FAISS search space toward items that *bridge the gap* (i.e. if the user adds a dry bread and a dry starter, the attention vector will organically drift toward a gravy Main Course or a Beverage to average out the meal).

### **Stage 3: Fine Ranking (Simulated DLRM + NLP Embeddings)**
The remaining 1000 items are run through a mathematically simulated Deep Learning Recommendation Model (DLRM).
1. We compute a focal dot product between a randomized `user_emb` (User Embedding based off their User ID trait seed) and the candidate embeddings.
2. **NLP Text Parsing**: The backend natively maps words inside the item's `Name` (such as "Spicy", "Chilly", "Masala") against the `user_spice_tolerance` factor.
3. If the user profile mathematically favors heat, and the NLP detects "Spicy", the item receives a massive linear weight boost!

### **Stage 4: Core Business Heuristics & Filters**
Finally, the Top 50 items are slammed against hardcoded business rules written purely in Pandas:
1. **Budget Restriction**: Recommends are capped to **40% of the active Cart's Total Value**. (We never want to suggest a ₹500 dish to someone checking out a ₹200 cart).
2. **Package Rule**: If the cart is enormous (> ₹600), the system actively boosts items marked `Size: Low` to balance the meal portions.
3. **Rating Multiplier**: The item's parent restaurant rating is referenced. If `RestRating >= 4.8`, the item is flagged as a "Hero" and its rank surges upwards.

The final **Top 5 Items** are converted to JSON with generated human-readable natural language explanations ("Perfect pairing!", "NLP Match: Maps to your High Spice User Embedding") and relayed back to the NGINX UI.

---

## 🏃 4. Software Engineering (SDE) Flow & User Journey

### A. The Customer Journey
*   **Authentication**: The Customer clicks "Login as Customer" (UI triggers `/login/user` mapping to `U0001`).
*   **Global Discovery**: The homepage sends a `GET /restaurants`, instantly parsed via the Redis cache. The user sees a pristine grid of multi-cuisine restaurants.
*   **Search Matrix**: The user types "Tikka" in the global search. A debounced Javascript hook sends `GET /search?q=Tikka`, iterating down the Pandas dataframe across the entire ecosystem.
*   **Local Restaurant Menu**: The user clicks a restaurant. The UI hides the home page layout. `GET /restaurants/{rest_id}/items` fires, pulling back exclusively that specific menu.
*   **The CSAO Injection**: The user clicks `Add` on a main course. The Local JS state (`app.js`) triggers `POST /recommend`. The 4-Stage AI pipeline executes locally in `<200ms`, feeding back the top 5 intelligent pairings that dynamically pop up on the sidebar visually!
*   **The Order Check**: The user clicks `Proceed to Pay`. `POST /order` fires, wiping the UI cart, saving the purchase array into `interactions.csv`, keeping a mathematical log of user behavior.

### B. The Restaurant Owner Journey
*   **Authentication**: The Owner clicks "Login as Restaurant Owner" (`/login/restaurant`).
*   **CRUD Dashboard**: The UI loads the Owner Dashboard. 
*   **Updating**: The Owner sees a typo in their item, clicks "Edit", changes the price, and hits Save. The frontend triggers `PUT /api/v1/items/{item_id}`.
*   **The Reaction**: Pandas physically mutates the `items.csv` file, updates RAM, recalculates completely new 64-dimensional embeddings for the catalog, refreshes FAISS, and intelligently drops all cached search queries from Redis instantaneously!

---

## 💾 5. Data Dictionaries (CSVs)

Since heavy databases were entirely ousted, CSVs act as physical persistence for the application when the container goes offline.

1.  **`items.csv`**: Over 2000 dynamically populated permutations of dishes spanning Main Courses, Starters, Breads, Beverages, Desserts, and Sides linked across 50 simulated Restaurants.
    *   *Columns: ItemID, RestID, Name, Price_INR, Is_Veg, Category, Image_URL, Meal_Time, Size*
2.  **`restaurants.csv`**: Contains mock logic for 50 distinct real-world locations, storing mock GPS lat/lon data, real categorical cuisines (Chinese, South Indian, Italian), and organic 1.0 - 5.0 ratings.
    *   *Columns: RestID, Cuisine, GPS_Lat, GPS_Long, Rating, Avg_Prep_Time_mins*
3.  **`users.csv`**: Simple mock matrix of standard users natively available for login testing.
    *   *Columns: UserID, Name, Tier, Registration_Date, Spice_Tolerance_Base*
4.  **`interactions.csv`**: Automatically generated and appended to whenever a user completes an overarching `Checkout` flow via the UI.
    *   *Columns: UserID, ItemID, InteractionType, Timestamp*

---

> Built rigorously for minimal spin-up time and maximized logical throughput. Designed via Project Titan.