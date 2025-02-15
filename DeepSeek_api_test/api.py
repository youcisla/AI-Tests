import os
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage
from azure.core.credentials import AzureKeyCredential

# Load environment variables from .env
load_dotenv()

# Use the original client creation without specifying region or extra headers.
client = ChatCompletionsClient(
    endpoint="https://models.github.ai/inference",
    credential=AzureKeyCredential(os.environ["GITHUB_TOKEN"]),
)

response = client.complete(
    messages=[UserMessage("Can you explain the basics of machine learning?")],
    model="DeepSeek-R1",
    max_tokens=2048,
)

print(response.choices[0].message.content)
