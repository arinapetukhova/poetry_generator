import requests
import os
from typing import List
import numpy as np

class Embedder:
    def __init__(self, model_api):
        self.api_url = model_api
        self.headers = {"Authorization": f"Bearer {os.environ.get('HUG_FACE', '')}"}
    
    def embed_to_list(self, text: str) -> List[float]:
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"inputs": text, "options": {"wait_for_model": True}}
            )
            if response.status_code == 200:
                return response.json().tolist() if hasattr(response.json(), 'tolist') else response.json()
            else:
                raise ConnectionError
        except:
            raise ConnectionError
    
    def embed_single(self, text: str) -> np.ndarray:
        return np.array(self.embed_to_list(text))
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        return np.array([self.embed_to_list(text) for text in texts])