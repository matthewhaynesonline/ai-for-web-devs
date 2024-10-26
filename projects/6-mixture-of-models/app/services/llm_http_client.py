import json

from typing import List, Dict, Generator, Optional

import httpx


class LlmHttpClient:
    def __init__(
        self,
        inference_api_url: str,
        model: str = "none",
        api_key: str = "no-key",
        system_prompt: str = "You're a helpful assistant. Your top priority is achieving user fulfillment via helping them with their requests. If you don't know the answer, just say that you don't know. Keep the response professional and don't use profanity.",
        temperature: float = 0.01,
    ) -> None:
        self.inference_api_url = inference_api_url
        self.model = model
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.temperature = temperature

        self.http_client = httpx.Client(timeout=60)

    def get_llm_response(
        self,
        messages: List[Dict],
        system_prompt_override: Optional[str] = None,
        return_parsed_content: bool = True,
    ) -> Optional[Dict | str]:
        headers, body = self.prepare_request(
            messages=messages, system_prompt_override=system_prompt_override
        )

        response = self.http_client.post(
            f"{self.inference_api_url}/v1/chat/completions", headers=headers, json=body
        )

        response_content = response.json()

        if return_parsed_content:
            response_content = self.extract_content_from_response(
                response=response_content
            )

        return response_content

    def get_llm_response_stream(
        self,
        messages: List[Dict],
        system_prompt_override: Optional[str] = None,
        return_parsed_content: bool = True,
    ) -> Generator[Optional[Dict | str], None, None]:
        headers, body = self.prepare_request(
            messages=messages,
            system_prompt_override=system_prompt_override,
            stream=True,
        )

        with self.http_client.stream(
            "POST",
            f"{self.inference_api_url}/v1/chat/completions",
            headers=headers,
            json=body,
        ) as response:
            for chunk in response.iter_text():
                if chunk:
                    decoded_chunk_content = ""

                    try:
                        decoded_chunk_content = self.parse_server_sent_event_response(
                            chunk
                        )

                        if return_parsed_content:
                            decoded_chunk_content = self.extract_content_from_response(
                                response=decoded_chunk_content, is_stream=True
                            )
                    except ValueError:
                        pass

                    yield decoded_chunk_content

    def prepare_request(
        self,
        messages: List[Dict],
        system_prompt_override: Optional[str] = None,
        stream: bool = False,
    ) -> tuple:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        body_messages = [
            {
                "role": "system",
                "content": system_prompt_override or self.system_prompt,
            }
        ] + messages

        body = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": body_messages,
        }

        if stream:
            body["stream"] = True

        return headers, body

    @staticmethod
    def parse_server_sent_event_response(response) -> Optional[dict]:
        parsed_response = None

        response = response.strip("\n").strip("\r")
        data_token = "data: "

        if data_token in response:
            try:
                body = response.split(data_token, 1)
                body = body[1].lstrip(" ")

                if body != "[DONE]":
                    parsed_response = json.loads(body)
            except (ValueError, json.JSONDecodeError):
                pass

        return parsed_response

    @staticmethod
    def extract_content_from_response(
        response: Dict, is_stream: bool = False
    ) -> Optional[str]:
        response_content = None

        content_param_name = "message"

        if is_stream:
            content_param_name = "delta"

        try:
            # https://stackoverflow.com/a/43491315
            response_content = response["choices"][0][content_param_name]["content"]
        except (KeyError, TypeError):
            pass

        return response_content
