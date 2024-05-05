from ollama import Client


class LlmClient:
    def __init__(self, ollama_instance_url: str, model: str):
        self.ollama_instance_url = ollama_instance_url
        self.model = model
        self.client = Client(host=ollama_instance_url)

    def get_llm_response(self, input: str = ""):
        response = self.client.generate(
            model=self.model,
            prompt=input,
        )
        output = response["response"]
        output = self.clean_output(output)

        return output

    def get_llm_response_stream(self, input: str = ""):
        response = self.client.generate(
            model=self.model,
            prompt=input,
            stream=True,
        )

        for chunk in response:
            output = chunk["response"]
            output = self.clean_output(output)

            yield output

    def clean_output(self, output: str) -> str:
        ending_token = "<|im_end|>"
        output = output.replace(ending_token, "")

        return output
