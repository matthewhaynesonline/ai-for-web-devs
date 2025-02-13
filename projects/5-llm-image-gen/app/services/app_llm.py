import json
import os
import sys

from pathlib import Path
from typing import Generator, List

from jinja2 import Template

from services.app_logger import AppLogger
from services.llm_http_client import LlmHttpClient
from services.vector_store import VectorStore

# TODO better way to do this (import from parent dir)?
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from models import ChatMessage, ChatMessageRole


class AppLlm:
    def __init__(
        self,
        llm_http_client: LlmHttpClient,
        vector_store: VectorStore,
        logger: AppLogger,
        debug: bool = False,
    ):
        self.llm_http_client = llm_http_client
        self.vector_store = vector_store
        self.logger = logger
        self.debug = debug

        self.prompt_templates_dir = Path(__file__).parent / "prompts"

        self.system_prompt = ""
        with open(f"{self.prompt_templates_dir}/system.j2", "r") as file:
            self.system_prompt = file.read()

        self.rag_prompt_template_string = ""
        with open(f"{self.prompt_templates_dir}/rag_with_sources.j2", "r") as file:
            self.rag_prompt_template_string = file.read()

        self.rag_prompt_template = Template(self.rag_prompt_template_string)

        self.chat_summary_prompt_template_string = ""
        with open(f"{self.prompt_templates_dir}/chat_summary.j2", "r") as file:
            self.chat_summary_prompt_template_string = file.read()

        self.chat_summary_prompt_template = Template(
            self.chat_summary_prompt_template_string
        )

    def get_llm_response(self, input: str = "", use_rag: bool = True) -> str:
        if use_rag:
            chat_prompt = self.get_rag_prompt(input)
        else:
            chat_prompt = input

        self.log_llm_messages(caller="get_llm_response", messages=[chat_prompt])

        response = self.llm_http_client.get_llm_response(
            prompt=chat_prompt, system_prompt_override=self.system_prompt
        )
        response_content = ""

        if response["choices"][0]["message"]["content"] is not None:
            response_content = response["choices"][0]["message"]["content"]
            response_content = self.clean_output(response_content)

        return response_content

    def get_llm_response_stream(
        self, input: str = "", use_rag: bool = True
    ) -> Generator[str, None, None]:
        if use_rag:
            chat_prompt = self.get_rag_prompt(input)
        else:
            chat_prompt = input

        self.log_llm_messages(caller="get_llm_response_stream", messages=[chat_prompt])

        response = self.llm_http_client.get_llm_response_stream(
            prompt=chat_prompt, system_prompt_override=self.system_prompt
        )

        for chunk in response:
            response_content = ""

            try:
                # https://stackoverflow.com/a/43491315
                chunk_content = chunk["choices"][0]["delta"]["content"]

                if chunk_content is not None:
                    response_content = self.clean_output(chunk_content)
            except (KeyError, TypeError):
                pass

            yield response_content

    def get_llm_chat_response_stream(
        self, messages: List[dict], use_rag: bool = True
    ) -> Generator[str, None, None]:
        messages = self.prepend_system_prompt_to_messages(messages=messages)

        if use_rag:
            messages = self.render_last_message_with_rag_prompt(messages=messages)

        self.log_llm_messages(caller="get_llm_chat_response_stream", messages=messages)

        response = self.llm_http_client.get_llm_chat_response_stream(
            messages=messages, system_prompt_override=self.system_prompt
        )

        for chunk in response:
            response_content = ""

            try:
                # https://stackoverflow.com/a/43491315
                chunk_content = chunk["choices"][0]["delta"]["content"]

                if chunk_content is not None:
                    response_content = self.clean_output(chunk_content)
            except (KeyError, TypeError):
                pass

            yield response_content

    def prepend_system_prompt_to_messages(self, messages: List[dict]) -> List[dict]:
        system_message = ChatMessage.convert_chat_message_to_llm_format(
            role=ChatMessageRole.SYSTEM.value, content=self.system_prompt
        )

        messages.insert(0, system_message)

        return messages

    def render_last_message_with_rag_prompt(self, messages: List[dict]) -> List[dict]:
        if messages[-1]["role"] != ChatMessageRole.USER.value:
            # this shouldn't happen
            raise
            return messages

        messages[-1]["content"] = self.get_rag_prompt(input=messages[-1]["content"])

        return messages

    def get_rag_prompt(self, input: str) -> str:
        context = self.get_relevant_context(input)

        chat_prompt = self.rag_prompt_template.render(
            {"question": input, "documents": context}
        )

        return chat_prompt

    def get_relevant_context(self, input: str, max_number_of_docs: int = 3) -> List:
        query_response = self.vector_store.query(text=input, size=max_number_of_docs)

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

    def get_chat_summary(self, chat_messages: List) -> str:
        chat_summary_prompt = self.chat_summary_prompt_template.render(
            {"chat_messages": chat_messages}
        )

        self.log_llm_messages(caller="get_chat_summary", messages=[chat_summary_prompt])

        response = self.llm_http_client.get_llm_response(
            prompt=chat_summary_prompt, system_prompt_override=self.system_prompt
        )
        response_content = ""

        if response["choices"][0]["message"]["content"] is not None:
            response_content = response["choices"][0]["message"]["content"]
            response_content = self.clean_output(response_content)

        return response_content

    def clean_output(self, output: str) -> str:
        LLM_TEMPLATE_TOKENS = ["<|end|>", "<|im_end|>"]

        for template_token in LLM_TEMPLATE_TOKENS:
            output = output.replace(template_token, "")

        return output

    def log_llm_messages(self, caller: str, messages: list) -> None:
        if not self.debug:
            return

        messages_json = json.dumps(messages, indent=2)
        log_message_content = f"{caller}:\n{messages_json}"

        self.logger.log(log_message_content)
