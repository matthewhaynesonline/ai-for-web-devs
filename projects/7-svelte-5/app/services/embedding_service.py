from typing import List

import httpx


class EmbeddingService:
    def __init__(
        self,
        inference_api_url: str,
        model: str = "none",
        encoding_format: str = "float",
        api_key: str = "no-key",
    ) -> None:
        self.inference_api_url = inference_api_url
        self.model = model
        self.encoding_format = encoding_format
        self.api_key = api_key

        self.http_client = httpx.Client(timeout=60)

        self.endpoint = f"{self.inference_api_url}/embeddings"
        self.embedding_model_dimensions = self.get_embedding_model_dimensions()

    def get_embedding_model_dimensions(self) -> int:
        embedding_model_dimensions = 0
        test_embeddings = self.get_embeddings("")
        embedding_model_dimensions = len(test_embeddings)

        return embedding_model_dimensions

    def get_embeddings(self, embedding_input: str) -> List:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        body = {
            "input": embedding_input,
            "model": self.model,
            "encoding_format": self.encoding_format,
        }

        response = self.http_client.post(self.endpoint, headers=headers, json=body)
        data = response.json()

        return data["data"][0]["embedding"]
