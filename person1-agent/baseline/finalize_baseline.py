import json
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(override=True)

api_key = os.getenv("ANTHROPIC_API_KEY")
model = os.getenv("CLAUDE_MODEL")

if not api_key:
    raise ValueError("ANTHROPIC_API_KEY is missing from .env")

if not model:
    raise ValueError("CLAUDE_MODEL is missing from .env")


# ============================================================
# 2. CREATE CLAUDE CLIENT
# ============================================================

client = Anthropic(api_key=api_key)


# ============================================================
# 3. RESULTS FOLDER
# ============================================================

script_dir = Path(__file__).resolve().parent

results_dir = (
    script_dir
    / ".."
    / "results"
    / "claude_baseline"
).resolve()

results_dir.mkdir(parents=True, exist_ok=True)


# ============================================================
# 4. PROMPT
#
# IMPORTANT:
# This is only finishing the Claude-only baseline.
#
# We DO NOT give Claude:
# - human-written tests
# - gcov results
# - uncovered branch feedback
#
# Those things belong to our smarter agent later.
# ============================================================

prompt = """
Complete the Claude-only grep testing baseline.

The original request was:

"You are a software developer. Please generate test inputs that can
achieve the maximum branch coverage for grep. See attached software
package."

You already analyzed the supplied GNU grep v0 package in the earlier
baseline run, but that response reached the maximum output-token limit
before returning the final test cases.

DO NOT analyze the source code again.
DO NOT compile anything.
DO NOT use tools.
DO NOT explain your reasoning.

Your only task now is to output the final grep test suite.

Tests will be executed from the grep/source directory.

The grep executable is:

../versions.alt/versions.orig/v0/grep.exe

Available input files include:

../inputs/grep0.dat
../inputs/grep1.dat
../inputs/grepBinary
../inputs/grepNull.dat
../inputs/grepDir/grep0.dat
../inputs/grepDir/grep1.dat
../inputs/grepDir/grepNull.dat

The program supports options including:

-0 -1 -2 -3 -4 -5 -6 -7 -8 -9
-A -B -C
-E -F -G -V -X
-b -c -e -f -h -i -L -l -n -q -s -v -w -x -y

Generate exactly 60 diverse test cases intended to maximize branch
coverage.

Include tests for:

- ordinary matching
- no-match behavior
- basic regular expressions
- extended regular expressions
- fixed-string matching
- case-insensitive matching
- old -y case-insensitive option
- whole-word matching
- whole-line matching
- inverted matching
- multiple -e patterns
- multiple files
- standard input
- context options -A, -B and -C
- numeric context options
- counting
- line numbers
- byte offsets
- quiet mode
- file listing with -l
- nonmatching file listing with -L
- suppressed errors with -s
- missing files
- invalid option combinations
- malformed regular expressions
- empty input files
- fixed strings containing regex characters
- matcher selection using -E, -F and -G
- unusual combinations of valid options

Return ONLY valid JSON.

Use EXACTLY this format:

{
  "tests": [
    {
      "id": "B001",
      "command": "../versions.alt/versions.orig/v0/grep.exe PATTERN ../inputs/grep0.dat",
      "category": "basic matching"
    }
  ]
}

Rules:

1. IDs must run from B001 through B060.
2. Each command must be a complete shell command.
3. Do not use Markdown code fences.
4. Do not write anything before the JSON.
5. Do not write anything after the JSON.
6. Do not invent input files other than the listed files.
"""


# ============================================================
# 5. CALL CLAUDE
#
# NO TOOLS ARE PROVIDED.
#
# Sonnet 5.5 supports between_tools + low effort.
# This prevents another huge source-analysis reasoning pass.
# ============================================================

print("Generating final Claude-only baseline tests...")
print("Model:", model)
print("No tools or code execution are enabled.\n")


request_args = {
    "model": model,
    "max_tokens": 9000,
    "messages": [
        {
            "role": "user",
            "content": prompt,
        }
    ],
}


# These settings are specifically supported by Sonnet 5.5.
if model == "claude-sonnet-5-5":
    request_args["thinking"] = {
        "type": "between_tools"
    }

    request_args["output_config"] = {
        "effort": "low"
    }


response = client.messages.create(**request_args)


# ============================================================
# 6. GET TEXT FROM CLAUDE
# ============================================================

text_parts = []

for block in response.content:
    if block.type == "text":
        text_parts.append(block.text)


raw_output = "\n".join(text_parts).strip()


# ============================================================
# 7. SAVE RAW RESPONSE FIRST
#
# This means even if JSON parsing fails, we do not lose Claude's
# generated tests.
# ============================================================

raw_file = results_dir / "baseline_tests_raw.txt"

with open(raw_file, "w", encoding="utf-8") as file:
    file.write(raw_output)


# ============================================================
# 8. CLEAN POSSIBLE MARKDOWN FENCES
# ============================================================

cleaned_output = raw_output.strip()

if cleaned_output.startswith("```json"):
    cleaned_output = cleaned_output[len("```json"):]

elif cleaned_output.startswith("```"):
    cleaned_output = cleaned_output[len("```"):]


if cleaned_output.endswith("```"):
    cleaned_output = cleaned_output[:-3]


cleaned_output = cleaned_output.strip()


# ============================================================
# 9. PARSE JSON
# ============================================================

try:
    data = json.loads(cleaned_output)

except json.JSONDecodeError as error:

    print("\n======================================")
    print("JSON PARSING FAILED")
    print("======================================")

    print(error)

    print("\nClaude's raw response was still saved here:")
    print(raw_file)

    print("\nStop reason:")
    print(response.stop_reason)

    raise SystemExit(1)


# ============================================================
# 10. VALIDATE TEST STRUCTURE
# ============================================================

if "tests" not in data:
    raise ValueError(
        "Claude returned JSON but there is no 'tests' array."
    )


tests = data["tests"]


if not isinstance(tests, list):
    raise ValueError("'tests' must be a list.")


# ============================================================
# 11. SAVE FINAL TESTS
# ============================================================

tests_file = results_dir / "baseline_tests.json"

with open(tests_file, "w", encoding="utf-8") as file:
    json.dump(
        data,
        file,
        indent=4,
    )


# ============================================================
# 12. SAVE API USAGE
# ============================================================

usage = {
    "model": model,
    "input_tokens": response.usage.input_tokens,
    "output_tokens": response.usage.output_tokens,
    "stop_reason": response.stop_reason,
    "number_of_tests": len(tests),
}


usage_file = results_dir / "final_retrieval_usage.json"

with open(usage_file, "w", encoding="utf-8") as file:
    json.dump(
        usage,
        file,
        indent=4,
    )


# ============================================================
# 13. SAVE COMPLETE RESPONSE
# ============================================================

response_file = results_dir / "final_retrieval_response.json"

with open(response_file, "w", encoding="utf-8") as file:
    file.write(response.to_json())


# ============================================================
# 14. PRINT SUMMARY
# ============================================================

print("======================================")
print("CLAUDE-ONLY BASELINE COMPLETE")
print("======================================")

print("Tests generated:", len(tests))
print("Input tokens:", response.usage.input_tokens)
print("Output tokens:", response.usage.output_tokens)
print("Stop reason:", response.stop_reason)

print("\nTests saved to:")
print(tests_file)


print("\nFirst 5 tests:\n")

for test in tests[:5]:

    print(
        test.get("id"),
        "-",
        test.get("command")
    )