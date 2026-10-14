import os

from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv(override=True)


class ClaudeClient:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model = os.getenv("CLAUDE_MODEL")

        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is missing from .env"
            )

        if not model:
            raise ValueError(
                "CLAUDE_MODEL is missing from .env"
            )

        self.model = model

        self.client = Anthropic(
            api_key=api_key
        )


    def generate(self, prompt, max_tokens=5000):
        """
        Send a prompt to Claude and return:
        - Claude's text response
        - token usage
        """

        request_args = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        # Keep Sonnet 5.5 calls efficient.
        if self.model == "claude-sonnet-5-5":
            request_args["thinking"] = {
                "type": "between_tools"
            }

            request_args["output_config"] = {
                "effort": "low"
            }


        response = self.client.messages.create(
            **request_args
        )


        text_parts = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)


        text = "\n".join(text_parts).strip()


        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "stop_reason": response.stop_reason,
        }


        return text, usage