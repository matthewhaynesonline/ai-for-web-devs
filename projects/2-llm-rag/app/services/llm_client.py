from ollama import Client


class LlmClient:
    def __init__(
        self, ollama_instance_url: str, model: str, embedding_function, vector_store
    ):
        self.ollama_instance_url = ollama_instance_url
        self.model = model
        self.embedding_function = embedding_function
        self.vector_store = vector_store

        self.client = Client(host=ollama_instance_url)

        self.prompt_base = """You are an assistant for question-answering tasks. \
        Use the following pieces of retrieved context to answer the question. \
        If you don't know the answer, just say that you don't know. \
        Use three sentences maximum and keep the answer concise.\
        """

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

        chat_prompt = f"""{self.prompt_base} \
        Question: {input} \
        Context: {context}
        Answer:\
        """

        return chat_prompt

    def get_relevant_context(self, input: str, max_number_of_docs: int = 3) -> str:
        query_response = self.vector_store.query_with_text(
            text=input, max_number_of_docs=max_number_of_docs
        )
        context_documents = query_response["documents"]
        context = ""

        if len(context_documents) == 1:
            if len(context_documents[0]) == 1:
                context = context_documents[0][0]
            else:
                for document in context_documents[0]:
                    context += "\n\n" + document
        else:
            raise

        return context

    def clean_output(self, chain_output: str) -> str:
        ending_token = "<|im_end|>"
        chain_output = chain_output.replace(ending_token, "")

        return chain_output
