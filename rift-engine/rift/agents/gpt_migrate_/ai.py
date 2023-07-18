from langchain.chat_models import ChatOpenAI
from .config import OPENAI_API_KEY
import os
import openai
from .utils import parse_code_string
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

@retry(wait=wait_random_exponential(min=40, max=60), stop=stop_after_attempt(20))
def completion_with_backoff(**kwargs):
    return openai.ChatCompletion.create(**kwargs)

openai.api_key = os.getenv("OPENAI_API_KEY")

class AI:
    def __init__(self, model="gpt-4", temperature=0.1, max_tokens=7000):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model_name = model
    
    def write_code(self, prompt):
        message=[{"role": "user", "content": str(prompt)}] 
        response = completion_with_backoff(
                messages=message,
                stream=False,
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
        if response["choices"][0]["message"]["content"].startswith("INSTRUCTIONS:"):
            return ("INSTRUCTIONS:","",response["choices"][0]["message"]["content"][14:])
        else:
            code_triples = parse_code_string(response["choices"][0]["message"]["content"])
            return code_triples

    def run(self, prompt):
        message=[{"role": "user", "content": str(prompt)}] 
        response = completion_with_backoff(
            messages=message,
            stream=True,
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        chat = ""
        for chunk in response:
            delta = chunk["choices"][0]["delta"]
            msg = delta.get("content", "")
            chat += msg
        return chat
    