import json

from typing import List

import httpx


class LlmHttpClient:
    def __init__(
        self,
        inference_api_url: str,
        model: str = "none",
        api_key: str = "no-key",
        system_prompt: str = "You're a helpful assistant. Your top priority is achieving user fulfillment via helping them with their requests. If you don't know the answer, just say that you don't know. Keep the response professional and don't use profanity.",
    ) -> None:
        self.inference_api_url = inference_api_url
        self.model = model
        self.api_key = api_key
        self.system_prompt = system_prompt

        self.http_client = httpx.Client(timeout=60)

        self.temperature = 0.01

    def get_llm_response(
        self, prompt: str, system_prompt_override: str | None = None
    ) -> List:
        system_prompt = self.system_prompt

        if system_prompt_override is not None:
            system_prompt = system_prompt_override

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        body = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }

        response = self.http_client.post(
            f"{self.inference_api_url}/v1/chat/completions", headers=headers, json=body
        )

        return response.json()

    def get_llm_response_stream(
        self, prompt: str, system_prompt_override: str | None = None
    ):
        system_prompt = self.system_prompt

        if system_prompt_override is not None:
            system_prompt = system_prompt_override

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        body = {
            "model": self.model,
            "temperature": self.temperature,
            "stream": True,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": prompt},
            ],
        }

        with self.http_client.stream(
            "POST",
            f"{self.inference_api_url}/v1/chat/completions",
            headers=headers,
            json=body,
        ) as response:
            for chunk in response.iter_text():
                if chunk:
                    decoded_chunk = self.parse_server_sent_event_response(chunk)
                    decoded_chunk = json.loads(decoded_chunk)

                    yield decoded_chunk

    def get_llm_chat_response_stream(
        self, messages: List[dict], system_prompt_override: str | None = None
    ):
        system_prompt = self.system_prompt

        if system_prompt_override is not None:
            system_prompt = system_prompt_override

        body_message = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        body_message += messages

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        body = {
            "model": self.model,
            "temperature": self.temperature,
            "stream": True,
            "messages": body_message,
        }

        with self.http_client.stream(
            "POST",
            f"{self.inference_api_url}/v1/chat/completions",
            headers=headers,
            json=body,
        ) as response:
            for chunk in response.iter_text():
                if chunk:
                    decoded_chunk = self.parse_server_sent_event_response(chunk)
                    decoded_chunk = json.loads(decoded_chunk)

                    yield decoded_chunk

    def parse_server_sent_event_response(self, response) -> str:
        parsed_response = ""

        response = response.strip("\n").strip("\r")

        data_token = "data: "
        if data_token in response:
            body = response.split(data_token, 1)
            parsed_response = body[1].lstrip(" ")

        return parsed_response
