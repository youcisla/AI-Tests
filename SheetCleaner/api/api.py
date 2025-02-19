# api.py
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq()

def get_ai_response(prompt: str) -> str:
    """
    Returns AI-generated text using the chat completion endpoint (non-streaming).
    """
    completion = client.chat.completions.create(
        model="deepseek-r1-distill-qwen-32b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=0.95,
        stream=False,  # Turn off streaming
        stop=None,
    )
    # When stream=False, 'completion' is a single dictionary with a 'choices' list.
    # For example:
    # {
    #   "choices": [
    #       {
    #           "message": {
    #               "role": "assistant",
    #               "content": "... AI response ..."
    #           }
    #       }
    #   ]
    # }
    return completion.choices[0].message.content

def get_ai_output(prompt: str, output_type: str = "text") -> str:
    """
    Returns AI output based on the prompt and the expected output type.
    For text output, it simply returns the generated text.
    For non-text outputs (image, video, or binary file), it is assumed the AI
    returns a base64 encoded string (also in non-streaming mode).
    """
    # Even for non-text, we use non-streaming for stability.
    completion = client.chat.completions.create(
        model="deepseek-r1-distill-qwen-32b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=0.95,
        stream=False,  # Turn off streaming
        stop=None,
    )
    return completion.choices[0].message.content
