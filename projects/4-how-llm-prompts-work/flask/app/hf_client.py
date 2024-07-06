import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, set_seed

# https://huggingface.co/docs/transformers/en/main_classes/tokenizer#transformers.PreTrainedTokenizer.__call__.return_tensors
# pt for pytorch


class HfClient:
    MODELS = [
        "TinyLlama/TinyLlama_v1.1",
        "microsoft/Phi-3-mini-4k-instruct",
        "meta-llama/Meta-Llama-3-8B-Instruct",
    ]

    TENSOR_TYPE = "pt"

    def __init__(self) -> None:
        self.model_id = self.MODELS[0]
        self.model = AutoModelForCausalLM.from_pretrained(self.model_id)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)

        self.max_new_tokens = 512
        self.temperature = 0.7

        self.messages = [
            {
                "role": "system",
                "content": "You are a pirate chatbot who always responds in pirate speak!",
            },
            {"role": "user", "content": "Hi."},
        ]

    def run(self):
        return self.llm_token_generate()

    def hf_run(self):
        result = pipeline("sentiment-analysis")("we love you")
        return result

    def llm_run_with_pipeline(self):
        pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
        )

        generation_args = {
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
        }

        result = pipe(self.messages, **generation_args)

        return result

    def llm_run(self):
        # https://huggingface.co/docs/transformers/en/conversations#what-happens-inside-the-pipeline
        formatted_chat = self.tokenizer.apply_chat_template(
            self.messages, tokenize=False, add_generation_prompt=True
        )

        tokenized_inputs = self.tokenizer(
            formatted_chat, return_tensors=self.TENSOR_TYPE, add_special_tokens=False
        )
        inputs = {
            key: tensor.to(self.model.device)
            for key, tensor in tokenized_inputs.items()
        }

        outputs = self.model.generate(
            **inputs, max_new_tokens=self.max_new_tokens, temperature=self.temperature
        )
        decoded_output = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].size(1) :], skip_special_tokens=True
        )

        result = decoded_output

        raise

        return result

    def llm_token_generate(self):
        # https://huggingface.co/blog/how-to-generate
        set_seed(42)

        input_text = "I enjoy walking with my cute dog"

        model_inputs = self.tokenizer(input_text, return_tensors=self.TENSOR_TYPE)

        sample_outputs = self.model.generate(
            **model_inputs,
            # max_new_tokens=self.max_new_tokens,
            max_new_tokens=1,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            num_return_sequences=10,
            temperature=self.temperature,
        )

        decoded_outputs = []

        for i, sample_output in enumerate(sample_outputs):
            decoded_outputs.append(
                self.tokenizer.decode(sample_output, skip_special_tokens=False)
            )

        raise
