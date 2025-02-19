import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq()

def get_ai_response(prompt: str) -> str:
    """
    Returns AI-generated text using the streaming chat completion endpoint.
    The function accumulates streamed chunks into a single response.
    """
    completion = client.chat.completions.create(
        model="qwen-2.5-32b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=0.95,
        stream=True,
        stop=None,
    )
    response = ""
    for chunk in completion:
        response += chunk.choices[0].delta.content or ""
    return response

def get_ai_output(prompt: str, output_type: str = "text") -> str:
    """
    Returns AI output based on the prompt and expected output type.
    For text output, it returns the accumulated streamed text.
    """
    completion = client.chat.completions.create(
        model="qwen-2.5-32b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=0.95,
        stream=True,
        stop=None,
    )
    response = ""
    for chunk in completion:
        response += chunk.choices[0].delta.content or ""
    return response
