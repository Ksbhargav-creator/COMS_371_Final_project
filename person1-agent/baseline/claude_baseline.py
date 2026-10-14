import json
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv


# --------------------------------------------------
# 1. Load API configuration
# --------------------------------------------------

load_dotenv(override=True)

api_key = os.getenv("ANTHROPIC_API_KEY")
model = os.getenv("CLAUDE_MODEL")

if not api_key:
    raise ValueError("ANTHROPIC_API_KEY is missing from .env")

if not model:
    raise ValueError("CLAUDE_MODEL is missing from .env")


# --------------------------------------------------
# 2. Create Claude client
# --------------------------------------------------

client = Anthropic(api_key=api_key)


# --------------------------------------------------
# 3. Locate grep.zip
# --------------------------------------------------

# Current project:
# COMP_S_3710_Final/
# ├── grep.zip
# └── person1-agent/
#     └── baseline/
#         └── claude_baseline.py

script_directory = Path(__file__).resolve().parent

grep_zip = (
    script_directory
    / ".."
    / ".."
    / "grep.zip"
).resolve()

if not grep_zip.exists():
    raise FileNotFoundError(
        f"Could not find grep.zip at:\n{grep_zip}"
    )

print("Found grep.zip:")
print(grep_zip)


# --------------------------------------------------
# 4. Exact professor baseline prompt
# --------------------------------------------------

prompt = (
    "You are a software developer. "
    "Please generate test inputs that can achieve the maximum "
    "branch coverage for grep. "
    "See attached software package."
)


# --------------------------------------------------
# 5. Upload grep.zip to Claude
# --------------------------------------------------

print("\nUploading grep.zip to Claude...")

uploaded_file = client.files.upload(
    file=grep_zip
)

print("Upload successful.")
print("File ID:", uploaded_file.id)


# --------------------------------------------------
# 6. Send baseline request
# --------------------------------------------------

print("\nSending Claude-only baseline request...")
print("Model:", model)

response = client.messages.create(
    model=model,
    max_tokens=6000,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                },
                {
                    "type": "container_upload",
                    "file_id": uploaded_file.id,
                },
            ],
        }
    ],
    tools=[
        {
            "type": "code_execution_20250825",
            "name": "code_execution",
        }
    ],
)


# --------------------------------------------------
# 7. Extract Claude's text response
# --------------------------------------------------

text_parts = []

for block in response.content:
    if block.type == "text":
        text_parts.append(block.text)

claude_output = "\n".join(text_parts)


# --------------------------------------------------
# 8. Create results directory
# --------------------------------------------------

results_directory = (
    script_directory
    / ".."
    / "results"
    / "claude_baseline"
).resolve()

results_directory.mkdir(
    parents=True,
    exist_ok=True,
)


# --------------------------------------------------
# 9. Save Claude output
# --------------------------------------------------

output_file = results_directory / "claude_output.txt"

with open(
    output_file,
    "w",
    encoding="utf-8",
) as file:
    file.write(claude_output)


# --------------------------------------------------
# 10. Save exact prompt
# --------------------------------------------------

prompt_file = results_directory / "prompt.txt"

with open(
    prompt_file,
    "w",
    encoding="utf-8",
) as file:
    file.write(prompt)


# --------------------------------------------------
# 11. Save token usage
# --------------------------------------------------

usage_data = {
    "model": model,
    "input_tokens": response.usage.input_tokens,
    "output_tokens": response.usage.output_tokens,
}

usage_file = results_directory / "usage.json"

with open(
    usage_file,
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        usage_data,
        file,
        indent=4,
    )


# --------------------------------------------------
# 12. Save full API response
# --------------------------------------------------

full_response_file = (
    results_directory
    / "full_response.json"
)

with open(
    full_response_file,
    "w",
    encoding="utf-8",
) as file:
    file.write(response.to_json())


# --------------------------------------------------
# 13. Print results
# --------------------------------------------------

print("\n========== CLAUDE BASELINE OUTPUT ==========\n")

print(claude_output)

print("\n========== TOKEN USAGE ==========")

print(
    "Input tokens:",
    response.usage.input_tokens,
)

print(
    "Output tokens:",
    response.usage.output_tokens,
)

print("\nResults saved in:")
print(results_directory)