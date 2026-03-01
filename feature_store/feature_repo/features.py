from datetime import timedelta
from feast import Entity, FeatureView, Field
from feast.types import Float32, String, Int64
from feast.infra.offline_providers.postgres import PostgreSQLSource

# --------------------------------------------------------------------------
# Entities
# --------------------------------------------------------------------------
user = Entity(name="user_id", join_keys=["UserID"], description="User identifier")
item = Entity(name="item_id", join_keys=["ItemID"], description="Item identifier")
session = Entity(name="session_id", join_keys=["SessionID"], description="Session identifier")

# --------------------------------------------------------------------------
# Data Sources (Points to Postgres)
# --------------------------------------------------------------------------
user_stats_source = PostgreSQLSource(
    name="user_stats_source",
    query="SELECT * FROM user_stats",
    timestamp_field="event_timestamp",
)

cart_stats_source = PostgreSQLSource(
    name="cart_stats_source",
    query="SELECT * FROM cart_stats",
    timestamp_field="event_timestamp",
)

# --------------------------------------------------------------------------
# Feature Views
# --------------------------------------------------------------------------

# Time Cyclical Encoding (Sine/Cosine over 24 hours) & OpenWeatherCraving mappings 
# are precomputed externally and stored in Postgres/Redis
user_context_view = FeatureView(
    name="user_context",
    entities=[user],
    ttl=timedelta(days=1),
    schema=[
        Field(name="time_sin", dtype=Float32),
        Field(name="time_cos", dtype=Float32),
        Field(name="weather_craving_score", dtype=Float32), # Generated via OpenWeatherMap mapping
        Field(name="session_vector_id", dtype=String), # L2 cache pointer
    ],
    online=True,
    source=user_stats_source,
    tags={"team": "kiingss"},
)

# Cart composition scoring with weighted variables
cart_composition_view = FeatureView(
    name="cart_composition",
    entities=[session],
    ttl=timedelta(hours=4),
    schema=[
        Field(name="main_weight", dtype=Float32),
        Field(name="bread_weight", dtype=Float32),
        Field(name="drink_weight", dtype=Float32),
        Field(name="dessert_weight", dtype=Float32),
        Field(name="cart_value_inr", dtype=Int64),
    ],
    online=True,
    source=cart_stats_source,
    tags={"team": "kiingss"},
)

# Note: Top 50 Global Items L1 cache is kept in-memory in the gateway/API layer 
# rather than retrieving it per request from Redis to save the 15ms Feast budget.
