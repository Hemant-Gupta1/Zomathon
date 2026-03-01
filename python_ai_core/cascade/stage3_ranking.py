from typing import List
import random

def pytorch_dlrm_predict(user_id: str, candidates: List[str]) -> List[str]:
    """
    Stage 3: DLRM Ranking (PyTorch removed for speed)
    Now uses pure python randomization for the stub.
    """
    # Dummy Re-Ranking just based on score stubs
    shuffled = candidates.copy()
    random.shuffle(shuffled)
    return shuffled[:50]
