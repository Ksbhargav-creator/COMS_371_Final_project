import os

from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv(override=True)

api_key = os.getenv("ANTHROPIC_API_KEY")
model = os.getenv("CLAUDE_MODEL")


if not api_key:
    raise ValueError("ANTHROPIC_API_KEY is missing from .env")

if not model:
    raise ValueError("CLAUDE_MODEL is missing from .env")


client = Anthropic(
    api_key=api_key
)


print("Sending a small test request to Claude...\n")


response = client.messages.create(
    model=model,
    max_tokens=100,
    messages=[
        {
            "role": "user",
            "content": "Reply with exactly: Claude API is working."
        }
    ]
)


for block in response.content:
    if block.type == "text":
        print(block.text)


print("\nToken usage:")
print("Input tokens:", response.usage.input_tokens)
print("Output tokens:", response.usage.output_tokens)