import json
from pathlib import Path

from claude_client import ClaudeClient


class TestGenerator:
    """
    Uses Claude to generate structured grep test cases.

    Later, coverage feedback can be passed in so Claude generates
    tests specifically targeting uncovered branches.
    """

    def __init__(self):
        self.claude = ClaudeClient()


    def generate_tests(
        self,
        number_of_tests=10,
        coverage_feedback=None,
    ):
        """
        Generate grep test cases.

        coverage_feedback:
            Optional information about uncovered branches.
            If None, Claude generates a broad initial batch.
        """

        prompt = f"""
You are part of an AI software-testing agent.

Your job is to generate test inputs for GNU grep v0 that are likely
to increase branch coverage.

Tests are run from the grep/source directory.

Executable:

../versions.alt/versions.orig/v0/grep.exe

Available input files:

../inputs/grep0.dat
../inputs/grep1.dat
../inputs/grepBinary
../inputs/grepNull.dat
../inputs/grepDir/grep0.dat
../inputs/grepDir/grep1.dat
../inputs/grepDir/grepNull.dat

Supported command-line options include:

-0 -1 -2 -3 -4 -5 -6 -7 -8 -9
-A -B -C
-E -F -G -V -X
-b -c -e -f -h -i -L -l -n -q -s -v -w -x -y

Generate exactly {number_of_tests} diverse tests.

Prioritize tests that exercise different program behaviors such as:

- basic matching
- no-match cases
- regular expressions
- extended regular expressions
- fixed strings
- option combinations
- context output
- multiple files
- stdin
- malformed patterns
- error handling
- missing files
- matcher selection
- empty inputs
- unusual combinations of options

"""

        # --------------------------------------------------
        # Add coverage feedback when available
        # --------------------------------------------------

        if coverage_feedback:
            prompt += f"""

IMPORTANT COVERAGE FEEDBACK:

The previous tests have already been executed.

The following branches or behaviors remain uncovered:

{coverage_feedback}

Generate tests specifically designed to exercise these uncovered areas.

Avoid simply repeating tests that already cover common behavior.
"""

        else:
            prompt += """

This is the initial generation round, so create a broad and diverse
set of tests covering different grep behaviors.
"""


        # --------------------------------------------------
        # Require machine-readable JSON
        # --------------------------------------------------

        prompt += """

Return ONLY valid JSON.

Use exactly this structure:

{
  "tests": [
    {
      "id": "AI001",
      "command": "../versions.alt/versions.orig/v0/grep.exe pattern ../inputs/grep0.dat",
      "category": "basic matching",
      "reason": "Targets the normal successful matching path"
    }
  ]
}

Rules:

1. Return exactly the requested number of tests.
2. Each command must be executable from grep/source.
3. Do not invent input files.
4. Do not include Markdown code fences.
5. Do not include explanations outside the JSON.
6. Tests may intentionally cause grep errors if they target error-handling branches.
"""


        # --------------------------------------------------
        # Call Claude
        # --------------------------------------------------

        max_output_tokens = max(
            4000,
            number_of_tests * 350
        )

        response_text, usage = self.claude.generate(
            prompt,
            max_tokens=max_output_tokens
        )


        # --------------------------------------------------
        # Clean accidental Markdown fences
        # --------------------------------------------------

        cleaned = response_text.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):]

        elif cleaned.startswith("```"):
            cleaned = cleaned[len("```"):]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()


        # --------------------------------------------------
        # Parse JSON
        # --------------------------------------------------

        try:
            data = json.loads(cleaned)

        except json.JSONDecodeError as error:
            print("Claude did not return valid JSON.")
            print(error)

            print("\nRaw Claude response:\n")
            print(response_text)

            return None, usage


        if "tests" not in data:
            print("ERROR: Claude JSON does not contain a 'tests' field.")
            return None, usage


        return data["tests"], usage



# ==========================================================
# SIMPLE TEST WHEN THIS FILE IS RUN DIRECTLY
# ==========================================================

if __name__ == "__main__":

    generator = TestGenerator()

    print("Generating initial grep tests...\n")

    tests, usage = generator.generate_tests(
        number_of_tests=5
    )


    if tests is None:
        raise SystemExit(1)


    print("Generated tests:\n")

    for test in tests:
        print(
            test["id"],
            "-",
            test["command"]
        )

        print(
            "   Category:",
            test.get("category")
        )

        print(
            "   Reason:",
            test.get("reason")
        )

        print()


    print("Usage:")
    print(usage)


    # ------------------------------------------------------
    # Save temporary generated tests
    # ------------------------------------------------------

    project_root = Path(__file__).resolve().parent.parent

    output_directory = project_root / "tests"

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_directory
        / "generated_tests.json"
    )


    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            {
                "tests": tests
            },
            file,
            indent=4
        )


    print("\nTests saved to:")
    print(output_file)