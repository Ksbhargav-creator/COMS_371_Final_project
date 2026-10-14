import json
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv


# --------------------------------------------------
# 1. Load environment variables
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
# 3. Find previous baseline response
# --------------------------------------------------

script_directory = Path(__file__).resolve().parent

results_directory = (
    script_directory
    / ".."
    / "results"
    / "claude_baseline"
).resolve()

previous_response_file = (
    results_directory
    / "full_response.json"
)

if not previous_response_file.exists():
    raise FileNotFoundError(
        "Could not find the previous baseline response:\n"
        f"{previous_response_file}"
    )


# --------------------------------------------------
# 4. Load previous response
# --------------------------------------------------

with open(
    previous_response_file,
    "r",
    encoding="utf-8",
) as file:
    previous_response = json.load(file)


previous_stop_reason = previous_response.get("stop_reason")

print("Previous stop reason:", previous_stop_reason)


# --------------------------------------------------
# 5. Get Claude container ID
# --------------------------------------------------

container_data = previous_response.get("container")

if not container_data:
    raise ValueError(
        "The previous response does not contain a container ID."
    )

if isinstance(container_data, dict):
    container_id = container_data.get("id")
else:
    container_id = str(container_data)


if not container_id:
    raise ValueError(
        "Could not extract the Claude container ID."
    )


print("Reusing container:")
print(container_id)


# --------------------------------------------------
# 6. Continuation prompt
# --------------------------------------------------

continuation_prompt = """
The previous Claude-only grep baseline request hit the maximum token
limit before producing the final test inputs.

Continue the same task using the grep package that is already available
in this container.

Do not perform another exhaustive analysis of the entire source code.

Now produce the concrete grep test inputs that you recommend for
maximizing branch coverage.

The tests must be runnable from the grep/source directory using:

../versions.alt/versions.orig/v0/grep.exe

Use the input files already available in ../inputs/ whenever useful.

Include tests covering a broad variety of:
- command-line options
- option combinations
- basic regular expressions
- extended regular expressions
- fixed-string matching
- case-insensitive matching
- word and whole-line matching
- inverted matching
- multiple patterns
- multiple files
- stdin
- context options
- counting
- file listing
- error conditions
- unusual and invalid regular expressions

Return the final tests in a clear numbered list.

For every test, provide:
1. the exact shell command
2. a short explanation of what behavior or branch category it targets

Do not spend the response re-analyzing the entire codebase.
The goal of this continuation is to produce the final executable tests.
"""


# --------------------------------------------------
# 7. Continue using SAME Claude container
# --------------------------------------------------

print("\nRequesting final baseline tests...")
print("Model:", model)


response = client.messages.create(
    container=container_id,
    model=model,
    max_tokens=12000,
    messages=[
        {
            "role": "user",
            "content": continuation_prompt,
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
# 8. Extract text
# --------------------------------------------------

text_parts = []

for block in response.content:
    if block.type == "text":
        text_parts.append(block.text)

final_output = "\n".join(text_parts)


# --------------------------------------------------
# 9. Save continuation output
# --------------------------------------------------

continued_output_file = (
    results_directory
    / "claude_output_continued.txt"
)

with open(
    continued_output_file,
    "w",
    encoding="utf-8",
) as file:
    file.write(final_output)


# --------------------------------------------------
# 10. Save full continuation response
# --------------------------------------------------

continued_response_file = (
    results_directory
    / "continued_response.json"
)

with open(
    continued_response_file,
    "w",
    encoding="utf-8",
) as file:
    file.write(response.to_json())


# --------------------------------------------------
# 11. Save continuation usage
# --------------------------------------------------

usage_data = {
    "model": model,
    "input_tokens": response.usage.input_tokens,
    "output_tokens": response.usage.output_tokens,
    "stop_reason": response.stop_reason,
}

continued_usage_file = (
    results_directory
    / "continued_usage.json"
)

with open(
    continued_usage_file,
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        usage_data,
        file,
        indent=4,
    )


# --------------------------------------------------
# 12. Print results
# --------------------------------------------------

print("\n========== FINAL BASELINE TESTS ==========\n")

print(final_output)

print("\n========== USAGE ==========")

print("Input tokens:", response.usage.input_tokens)
print("Output tokens:", response.usage.output_tokens)
print("Stop reason:", response.stop_reason)

print("\nSaved final tests to:")
print(continued_output_file)