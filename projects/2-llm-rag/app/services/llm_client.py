from pathlib import Path

from jinja2 import Template
from ollama import Client


class LlmClient:
    def __init__(
        self, ollama_instance_url: str, model: str, embedding_function, vector_store
    ):
        self.ollama_instance_url = ollama_instance_url
        self.model = model
        self.embedding_function = embedding_function
        self.client = Client(host=ollama_instance_url)

        self.vector_store = vector_store

        self.prompt_templates_dir = Path(__file__).parent / "prompts"

        self.prompt_template_string = ""
        with open(f"{self.prompt_templates_dir}/simple_rag.j2", "r") as file:
            self.prompt_template_string = file.read()

        self.prompt_template = Template(self.prompt_template_string)

    def get_llm_response(self, input: str = ""):
        chat_prompt = self.get_chat_prompt(input)
        response = self.client.generate(model=self.model, prompt=chat_prompt)
        output = response["response"]
        output = self.clean_output(output)

        return output

    def get_llm_response_stream(self, input: str = ""):
        chat_prompt = self.get_chat_prompt(input)
        response = self.client.generate(
            model=self.model, prompt=chat_prompt, stream=True
        )

        for chunk in response:
            output = chunk["response"]
            output = self.clean_output(output)

            yield output

    def get_chat_prompt(self, input: str):
        context = self.get_relevant_context(input)

        chat_prompt = self.prompt_template.render(
            {"question": input, "context": context}
        )

        return chat_prompt

    def get_relevant_context(self, input: str, max_number_of_docs: int = 3):
        query_response = self.vector_store.query(text=input, size=max_number_of_docs)

        context = ""

        if len(query_response) > 0:
            for document in query_response:
                for content in document["fields"]["page_content"]:
                    context += content

        return context

    def clean_output(self, output: str) -> str:
        ending_token = "<|im_end|>"
        output = output.replace(ending_token, "")

        return output
