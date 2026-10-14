import json
from pathlib import Path

from test_generator import TestGenerator


# ==========================================================
# CONFIGURATION
# ==========================================================

ROUND6_TEST_COUNT = 30


# ==========================================================
# PROJECT PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TESTS_DIRECTORY = PROJECT_ROOT / "tests"
RESULTS_DIRECTORY = PROJECT_ROOT / "results"

TESTS_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)

RESULTS_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# FILE PATHS
# ==========================================================

ROUND1_TESTS_FILE = (
    TESTS_DIRECTORY
    / "agent_initial_tests.json"
)

ROUND2_TESTS_FILE = (
    TESTS_DIRECTORY
    / "agent_targeted_tests.json"
)

ROUND3_TESTS_FILE = (
    TESTS_DIRECTORY
    / "agent_round3_tests.json"
)

ROUND4_TESTS_FILE = (
    TESTS_DIRECTORY
    / "agent_round4_tests.json"
)

ROUND5_TESTS_FILE = (
    TESTS_DIRECTORY
    / "agent_round5_tests.json"
)

ROUND6_FEEDBACK_FILE = (
    RESULTS_DIRECTORY
    / "coverage_feedback_round6.txt"
)

ROUND6_TESTS_FILE = (
    TESTS_DIRECTORY
    / "agent_round6_tests.json"
)

USAGE_FILE = (
    RESULTS_DIRECTORY
    / "agent_usage.json"
)


# ==========================================================
# FILE HELPERS
# ==========================================================

def save_tests(tests, output_file):

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


def load_tests(input_file):

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    return data.get("tests", [])


def read_feedback(feedback_file):

    if not feedback_file.exists():
        return None

    with open(
        feedback_file,
        "r",
        encoding="utf-8"
    ) as file:

        feedback = file.read().strip()

    if not feedback:
        return None

    return feedback


# ==========================================================
# API USAGE
# ==========================================================

def load_usage():

    if not USAGE_FILE.exists():
        return []

    try:

        with open(
            USAGE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return data

    except (
        json.JSONDecodeError,
        OSError
    ):
        pass

    return []


def save_usage(usage_records):

    with open(
        USAGE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            usage_records,
            file,
            indent=4
        )


# ==========================================================
# TEST HELPERS
# ==========================================================

def assign_round_ids(
    tests,
    prefix
):

    for index, test in enumerate(
        tests,
        start=1
    ):

        test["id"] = (
            f"{prefix}{index:03d}"
        )

    return tests


def show_tests(tests):

    for test in tests:

        print(
            test.get("id"),
            "-",
            test.get("command")
        )

        print(
            "  Category:",
            test.get("category")
        )

        print(
            "  Reason:",
            test.get("reason")
        )

        print()


# ==========================================================
# COMMAND VALIDATION
# ==========================================================

def validate_commands(tests):

    problems = []

    for test in tests:

        command = test.get(
            "command",
            ""
        )

        grep_count = command.count(
            "grep.exe"
        )

        if grep_count != 1:

            problems.append(
                {
                    "id": test.get("id"),
                    "problem": (
                        "Expected exactly one grep.exe execution"
                    ),
                    "command": command
                }
            )

        if ";" in command:

            problems.append(
                {
                    "id": test.get("id"),
                    "problem": (
                        "Command contains a semicolon"
                    ),
                    "command": command
                }
            )

        if "&&" in command:

            problems.append(
                {
                    "id": test.get("id"),
                    "problem": (
                        "Command contains &&"
                    ),
                    "command": command
                }
            )

        if "||" in command:

            problems.append(
                {
                    "id": test.get("id"),
                    "problem": (
                        "Command contains ||"
                    ),
                    "command": command
                }
            )

    return problems


# ==========================================================
# CHECK EXISTING ROUND
# ==========================================================

def show_existing_round(
    round_number,
    test_file,
    expected_count=None
):

    if not test_file.exists():

        print(
            f"Round {round_number} tests are missing:"
        )

        print(
            test_file
        )

        return False


    tests = load_tests(
        test_file
    )


    print(
        f"Round {round_number}: "
        f"{len(tests)} existing tests found."
    )


    if (
        expected_count is not None
        and len(tests) != expected_count
    ):

        print(
            f"WARNING: Expected {expected_count} "
            f"tests for Round {round_number}, "
            f"but found {len(tests)}."
        )


    return True


# ==========================================================
# GENERATE ROUND 6
# ==========================================================

def generate_round6(
    generator,
    usage_records
):

    print("\n======================================")
    print("ROUND 6")
    print("======================================\n")


    # ------------------------------------------------------
    # Protect API budget
    # ------------------------------------------------------

    if ROUND6_TESTS_FILE.exists():

        print(
            "Existing Round 6 tests found."
        )

        print(
            "Claude will NOT be called again."
        )

        print(
            "This protects the limited API budget.\n"
        )


        tests = load_tests(
            ROUND6_TESTS_FILE
        )


        print(
            "Loaded",
            len(tests),
            "Round 6 tests."
        )


        return tests


    # ------------------------------------------------------
    # Read new Round 6 feedback
    # ------------------------------------------------------

    feedback = read_feedback(
        ROUND6_FEEDBACK_FILE
    )


    if not feedback:

        print(
            "Round 6 feedback file is missing or empty:"
        )

        print(
            ROUND6_FEEDBACK_FILE
        )

        return None


    # ------------------------------------------------------
    # Generate final targeted tests
    # ------------------------------------------------------

    print(
        "Generating FINAL targeted Round 6 tests..."
    )

    print(
        "Current cumulative coverage: 56.42%"
    )

    print(
        "Using the latest Round 5 uncovered-branch feedback."
    )

    print(
        "Requested tests:",
        ROUND6_TEST_COUNT
    )

    print()


    tests, usage = (
        generator.generate_tests(
            number_of_tests=ROUND6_TEST_COUNT,
            coverage_feedback=feedback
        )
    )


    if tests is None:

        print(
            "ERROR: Round 6 generation failed."
        )

        return None


    # ------------------------------------------------------
    # Verify number returned
    # ------------------------------------------------------

    if len(tests) != ROUND6_TEST_COUNT:

        print(
            "\nWARNING:"
        )

        print(
            f"Requested {ROUND6_TEST_COUNT} tests, "
            f"but Claude returned {len(tests)}."
        )

        print(
            "Review the generated tests before "
            "coverage measurement.\n"
        )


    # ------------------------------------------------------
    # IDs
    # ------------------------------------------------------

    tests = assign_round_ids(
        tests,
        "R6-"
    )


    # ------------------------------------------------------
    # Validate
    # ------------------------------------------------------

    problems = validate_commands(
        tests
    )


    if problems:

        print(
            "\nWARNING:"
        )

        print(
            "Some Round 6 commands need review.\n"
        )


        for problem in problems:

            print(
                problem["id"],
                "-",
                problem["problem"]
            )

            print(
                "Command:",
                problem["command"]
            )

            print()

    else:

        print(
            "Command validation passed."
        )

        print(
            "Each test contains exactly one "
            "grep.exe execution.\n"
        )


    # ------------------------------------------------------
    # Save tests
    # ------------------------------------------------------

    save_tests(
        tests,
        ROUND6_TESTS_FILE
    )


    # ------------------------------------------------------
    # Save usage
    # ------------------------------------------------------

    usage_records.append(
        {
            "round": 6,
            "type": (
                "final_uncovered_branch_optimization"
            ),
            "coverage_before_round": 56.42,
            "requested_tests": ROUND6_TEST_COUNT,
            "generated_tests": len(tests),
            **usage
        }
    )


    save_usage(
        usage_records
    )


    return tests


# ==========================================================
# MAIN
# ==========================================================

def main():

    generator = TestGenerator()

    usage_records = load_usage()


    print("======================================")
    print("GREP COVERAGE-GUIDED AI TEST AGENT")
    print("======================================\n")


    # ======================================================
    # VERIFY ROUNDS 1-5
    # ======================================================

    print("Existing experiment history:\n")


    round1_ok = show_existing_round(
        1,
        ROUND1_TESTS_FILE,
        10
    )

    round2_ok = show_existing_round(
        2,
        ROUND2_TESTS_FILE,
        10
    )

    round3_ok = show_existing_round(
        3,
        ROUND3_TESTS_FILE,
        10
    )

    round4_ok = show_existing_round(
        4,
        ROUND4_TESTS_FILE,
        10
    )

    round5_ok = show_existing_round(
        5,
        ROUND5_TESTS_FILE,
        30
    )


    if not (
        round1_ok
        and round2_ok
        and round3_ok
        and round4_ok
        and round5_ok
    ):

        print(
            "\nERROR:"
        )

        print(
            "Rounds 1 through 5 must exist "
            "before generating Round 6."
        )

        return


    # ======================================================
    # COVERAGE HISTORY
    # ======================================================

    print("\n======================================")
    print("COVERAGE HISTORY")
    print("======================================\n")


    print(
        "Claude-only baseline: 39.55%"
    )

    print(
        "Round 1: 34.16%"
    )

    print(
        "Round 2: 35.73%"
    )

    print(
        "Round 3: 37.79%"
    )

    print(
        "Round 4: 44.59%"
    )

    print(
        "Round 5: 56.42%"
    )


    print(
        "\nRound 5 improvement over Round 4:"
    )

    print(
        "+11.83 percentage points"
    )


    print(
        "\nRound 5 improvement over Claude baseline:"
    )

    print(
        "+16.87 percentage points"
    )


    print(
        "\nRound 6 strategy:"
    )

    print(
        "Target branch outcomes still uncovered "
        "after the 70-test cumulative run."
    )


    # ======================================================
    # GENERATE ROUND 6
    # ======================================================

    round6_tests = generate_round6(
        generator,
        usage_records
    )


    if round6_tests is None:

        return


    # ======================================================
    # SHOW TESTS
    # ======================================================

    print("\n======================================")
    print("ROUND 6 TESTS")
    print("======================================\n")


    show_tests(
        round6_tests
    )


    print(
        "Round 6 tests saved to:"
    )

    print(
        ROUND6_TESTS_FILE
    )


    print(
        "\nAPI usage saved to:"
    )

    print(
        USAGE_FILE
    )


    # ======================================================
    # FINAL SUMMARY
    # ======================================================

    print("\n======================================")
    print("ROUND 6 GENERATION COMPLETE")
    print("======================================\n")


    print(
        "Coverage before Round 6: 56.42%"
    )


    print(
        "\nNew Round 6 tests:"
    )

    print(
        len(round6_tests)
    )


    print(
        "\nCumulative test count after Round 6:"
    )

    print(
        "Round 1: 10"
    )

    print(
        "Round 2: 10"
    )

    print(
        "Round 3: 10"
    )

    print(
        "Round 4: 10"
    )

    print(
        "Round 5: 30"
    )

    print(
        "Round 6: 30"
    )

    print(
        "TOTAL: 100 agent-generated tests"
    )


    print(
        "\nNext step:"
    )

    print(
        "Send agent_round6_tests.json to Person 2."
    )

    print(
        "Person 2 should RESET coverage and run "
        "Rounds 1 through 6 cumulatively."
    )

    print(
        "\nDo NOT measure Round 6 by itself."
    )


# ==========================================================
# START PROGRAM
# ==========================================================

if __name__ == "__main__":
    main()