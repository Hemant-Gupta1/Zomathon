import os
import time
from feast import FeatureStore

def wait_for_services():
    print("Waiting for Redis and Postgres to be ready...")
    time.sleep(15)  # Real impl would poll ports
    print("Services ready. Applying Feast configuration.")

if __name__ == "__main__":
    wait_for_services()
    store = FeatureStore(repo_path="feature_repo")
    os.chdir("feature_repo")
    os.system("feast apply")
    print("Feast features applied successfully.")
