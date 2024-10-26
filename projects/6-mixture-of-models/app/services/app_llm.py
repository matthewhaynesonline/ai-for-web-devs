import json
import os
import sys


from functools import cached_property
from pathlib import Path
from typing import Dict, Generator, List, Optional, Type

from jinja2 import Template

from services.app_logger import AppLogger
from services.llm_http_client import LlmHttpClient
from services.content_store import ContentStore
from services.response_types import ResponseTypesFlags

# TODO better way to do this (import from parent dir)?
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from models import ChatMessage, ChatMessageRole


class AppLlm:
    def __init__(
        self,
        inference_small_api_url: str,
        llm_http_client: LlmHttpClient,
        content_store: ContentStore,
        logger: AppLogger,
        debug: bool = False,
    ):
        self.inference_small_api_url = inference_small_api_url
        self.llm_http_client = llm_http_client
        self.content_store = content_store
        self.logger = logger
        self.debug = debug

        self.prompt_templates_dir = Path(__file__).parent / "prompts"
        self.prompt_template_file_extension = ".j2"

        self.prompts = [
            os.path.splitext(template_file)[0]
            for template_file in os.listdir(self.prompt_templates_dir)
            if template_file.endswith(self.prompt_template_file_extension)
        ]

        self.prompt_templates = {}

        for prompt in self.prompts:
            template_string = ""

            with open(
                f"{self.prompt_templates_dir}/{prompt}{self.prompt_template_file_extension}",
                "r",
            ) as file:
                template_string = file.read()

            template = Template(template_string)

            self.prompt_templates[prompt] = {
                "template_string": template_string,
                "template": template,
            }

        self.system_prompt = self.prompt_templates["system"]["template_string"]

    ############
    # Classifier
    ############
    @cached_property
    def classifier_response_format(self) -> Dict:
        fields = ResponseTypesFlags.__annotations__.keys()

        properties = {field: {"title": field, "type": "boolean"} for field in fields}

        response_format = {
            "type": "json_object",
            "schema": {
                "properties": properties,
            },
            "required": list(fields),
        }

        return response_format

    def classify_message(self, message: str = "") -> Optional[ResponseTypesFlags]:
        system_prompt_override = "You are a helpful assistant designed to output JSON."

        message = self.prompt_templates["message_classifier"]["template"].render(
            {"message": message}
        )

        message = ChatMessage.convert_chat_message_to_llm_format(
            role=ChatMessageRole.USER.value, content=message
        )

        self.log_llm_messages(caller="classify_message", messages=[message])
        response = self.llm_http_client.get_llm_response(
            messages=[message],
            system_prompt_override=system_prompt_override,
            response_format=self.classifier_response_format,
            inference_api_url_override=self.inference_small_api_url,
        )

        response_content = None

        if response is not None:
            response_content = json.loads(response)
            response_content = ResponseTypesFlags(**response_content)

        return response_content

    ##################
    # Image Gen Helper
    ##################
    def get_diffusion_prompt_from_input(self, input: str = "") -> str:
        diffusion_prompt = self.prompt_templates["diffusion_prompt_from_message"][
            "template"
        ].render({"message": input})

        self.log_llm_messages(caller="get_chat_summary", messages=[diffusion_prompt])
        response_content = self.get_llm_response_for_single_message(
            content=diffusion_prompt,
            system_prompt_override="You are a helpful assistant.",
        )

        return response_content

    ############
    # LLM Calls
    ############
    def get_llm_response(self, input: str = "", use_rag: bool = True) -> str:
        chat_prompt = input

        if use_rag:
            chat_prompt = self.get_rag_prompt(input)

        self.log_llm_messages(caller="get_llm_response", messages=[chat_prompt])
        response_content = self.get_llm_response_for_single_message(content=chat_prompt)

        return response_content

    def get_llm_response_stream(
        self, messages: List[dict], use_rag: bool = True
    ) -> Generator[str, None, None]:
        if use_rag:
            messages = self.render_last_message_with_rag_prompt(messages=messages)

        self.log_llm_messages(caller="get_llm_chat_response_stream", messages=messages)
        response = self.llm_http_client.get_llm_response_stream(
            messages=messages, system_prompt_override=self.system_prompt
        )

        for chunk in response:
            response_content = ""

            try:
                if chunk is not None:
                    response_content = self.clean_output(chunk)
            except (KeyError, TypeError):
                pass

            yield response_content

    def get_chat_summary(self, chat_messages: List) -> str:
        chat_summary_prompt = self.prompt_templates["chat_summary"]["template"].render(
            {"chat_messages": chat_messages}
        )

        self.log_llm_messages(caller="get_chat_summary", messages=[chat_summary_prompt])
        response_content = self.get_llm_response_for_single_message(
            content=chat_summary_prompt
        )

        return response_content

    def get_llm_response_for_single_message(
        self, content: str, system_prompt_override: Optional[str] = None
    ) -> str:
        system_prompt = system_prompt_override or self.system_prompt

        message = ChatMessage.convert_chat_message_to_llm_format(
            role=ChatMessageRole.USER.value, content=content
        )

        response = self.llm_http_client.get_llm_response(
            messages=[message], system_prompt_override=system_prompt
        )

        response_content = ""

        if response is not None:
            response_content = self.clean_output(response)

        return response_content

    ######
    # RAG
    ######
    def get_rag_prompt(self, input: str) -> str:
        context = self.get_relevant_context(input)

        chat_prompt = self.prompt_templates["rag_with_sources"]["template"].render(
            {"question": input, "documents": context}
        )

        return chat_prompt

    def get_relevant_context(self, input: str, max_number_of_docs: int = 3) -> List:
        query_response = self.content_store.query(text=input, size=max_number_of_docs)

        context = []

        if len(query_response) > 0:
            for document in query_response:
                context.append(
                    {
                        "content": document["fields"]["page_content"],
                        "source": document["fields"]["metadata.source"],
                    }
                )

        return context

    def render_last_message_with_rag_prompt(self, messages: List[dict]) -> List[dict]:
        if messages[-1]["role"] != ChatMessageRole.USER.value:
            # this shouldn't happen
            raise
            return messages

        messages[-1]["content"] = self.get_rag_prompt(input=messages[-1]["content"])

        return messages

    ########
    # Utils
    ########
    def log_llm_messages(self, caller: str, messages: list) -> None:
        if not self.debug:
            return

        messages_json = json.dumps(messages, indent=2)
        log_message_content = f"{caller}:\n{messages_json}"

        self.logger.log(log_message_content)

    @staticmethod
    def clean_output(output: str) -> str:
        LLM_TEMPLATE_TOKENS = ["<|end|>", "<|im_end|>"]

        for template_token in LLM_TEMPLATE_TOKENS:
            output = output.replace(template_token, "")

        return output
