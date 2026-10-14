import os

from anthropic import Anthropic
from dotenv import load_dotenv


# Load variables from the .env file
load_dotenv(override=True)

api_key = os.getenv("ANTHROPIC_API_KEY")


# Make sure the API key exists
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY was not found.")
    print("Check your .env file.")
    raise SystemExit(1)


# Safe debugging information
# This does NOT print your full API key.
print("API key found.")
print("Key length:", len(api_key))
print("Key begins with:", api_key[:7])


# Create Claude client
client = Anthropic(
    api_key=api_key
)


print("\nTrying to connect to Claude...")
print("Checking available models...\n")


try:
    models = client.models.list()

    if not models.data:
        print("Connection worked, but no models were returned.")
    else:
        print("SUCCESS! Claude API connection is working.\n")
        print("Available models:")

        for model in models.data:
            print("-", model.id)


except Exception as error:
    print("ERROR: Could not connect to Claude.\n")
    print(error)

    print("\nPossible reasons:")
    print("1. The API key in .env is incorrect.")
    print("2. The API key has expired.")
    print("3. Your class uses a special Claude API endpoint or gateway.")
    print("4. There may be extra spaces or quotation marks in the .env file.")