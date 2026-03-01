import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 1. Config & Setup
# ---------------------------------------------------------
NUM_USERS = 200
NUM_RESTAURANTS = 50
NUM_ITEMS = 300
NUM_SESSIONS = 500 # Will generate roughly 1500-2000 interaction rows

cities = ['Tier 1', 'Tier 2', 'Tier 3']
genders = ['M', 'F']
categories = ['Starter', 'Main Course', 'Bread', 'Sides', 'Dessert', 'Beverage', 'Misc']

# ---------------------------------------------------------
# 2. Generate Users (Pareto logic applied later in interactions)
# ---------------------------------------------------------
users = []
for i in range(1, NUM_USERS + 1):
    users.append({
        'UserID': f'U{i:04d}',
        'Age': int(np.random.normal(26, 5)), # Centered around 26
        'Gender': np.random.choice(genders, p=[0.6, 0.4]),
        'Veg_Score': round(random.uniform(0, 1), 2),
        'City_Tier': np.random.choice(cities, p=[0.5, 0.3, 0.2]),
        'Price_Sensitivity': np.random.choice(['Low', 'Medium', 'High'])
    })
users_df = pd.DataFrame(users)
users_df['Age'] = users_df['Age'].clip(18, 60) # Ensure realistic ages

# ---------------------------------------------------------
# 3. Generate Restaurants
# ---------------------------------------------------------
restaurants = []
cuisines = ['North Indian', 'South Indian', 'Chinese', 'Bakery', 'Italian', 'Street Food']
for i in range(1, NUM_RESTAURANTS + 1):
    restaurants.append({
        'RestID': f'R{i:03d}',
        'Cuisine': random.choice(cuisines),
        'GPS_Lat': round(random.uniform(28.4, 28.7), 4), # Delhi NCR cluster
        'GPS_Long': round(random.uniform(77.1, 77.5), 4),
        'Rating': round(random.uniform(3.5, 5.0), 1),
        'Avg_Prep_Time_mins': random.randint(10, 45)
    })
rests_df = pd.DataFrame(restaurants)

# ---------------------------------------------------------
# 4. Generate Items (Long Tail Pricing)
# ---------------------------------------------------------
items = []
for i in range(1, NUM_ITEMS + 1):
    rest_id = random.choice(rests_df['RestID'])
    is_veg = np.random.choice([0, 1], p=[0.4, 0.6])
    category = random.choice(categories)
    # Log-normal distribution for prices
    price = int(np.random.lognormal(mean=5.0, sigma=0.8)) 
    price = max(30, min(price, 1500)) # Cap prices between 30 and 1500
    
    items.append({
        'ItemID': f'I{i:04d}',
        'RestID': rest_id,
        'Name': f'Simulated {category} {i}',
        'Price_INR': price,
        'Is_Veg': is_veg,
        'Category': category,
        'Image_URL': f'/img/mock_{i}.jpg'
    })
items_df = pd.DataFrame(items)

# ---------------------------------------------------------
# 5. Generate Interactions (Markov Chain Meal Progression)
# ---------------------------------------------------------
# Pareto distribution: 20% of users do 80% of the ordering
power_users = list(users_df['UserID'][:int(NUM_USERS * 0.2)])
casual_users = list(users_df['UserID'][int(NUM_USERS * 0.2):])

interactions = []
start_time = datetime(2026, 3, 1, 12, 0, 0)

for session_idx in range(1, NUM_SESSIONS + 1):
    # Select user based on Pareto principle
    if random.random() < 0.8:
        uid = random.choice(power_users)
    else:
        uid = random.choice(casual_users)
        
    session_id = f'S{session_idx:05d}'
    
    # Simulate time peaks (Lunch 1PM or Dinner 8PM)
    hour_offset = int(np.random.choice([1, 8, -2, 4], p=[0.4, 0.4, 0.1, 0.1]))
    current_time = start_time + timedelta(hours=hour_offset, minutes=random.randint(0, 59))
    
    cart_state = []
    # Pick a random restaurant for this session
    session_rest = random.choice(rests_df['RestID'])
    available_items = items_df[items_df['RestID'] == session_rest]['ItemID'].tolist()
    
    if not available_items:
        continue # Skip if rest has no items

    # Simulate 2 to 6 actions per session
    num_actions = random.randint(2, 6)
    
    for action_step in range(num_actions):
        current_time += timedelta(seconds=random.randint(10, 60))
        item = random.choice(available_items)
        
        # View or Add logic
        event = np.random.choice(['View', 'Add'], p=[0.6, 0.4])
        
        if event == 'Add':
            cart_state.append(item)
            
        interactions.append({
            'SessionID': session_id,
            'UserID': uid,
            'Timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'Event': event,
            'ItemID': item,
            'Cart_State': str(cart_state.copy())
        })
        
    # Final Checkout Action if cart isn't empty
    if cart_state:
        current_time += timedelta(seconds=random.randint(30, 120))
        interactions.append({
            'SessionID': session_id,
            'UserID': uid,
            'Timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'Event': 'Buy',
            'ItemID': 'NULL',
            'Cart_State': str(cart_state)
        })

interactions_df = pd.DataFrame(interactions)

# ---------------------------------------------------------
# 6. Export to CSV
# ---------------------------------------------------------
users_df.to_csv('users.csv', index=False)
rests_df.to_csv('restaurants.csv', index=False)
items_df.to_csv('items.csv', index=False)
interactions_df.to_csv('interactions.csv', index=False)

print(f"Success! Generated {len(users_df)} users, {len(rests_df)} restaurants, {len(items_df)} items, and {len(interactions_df)} interactions.")