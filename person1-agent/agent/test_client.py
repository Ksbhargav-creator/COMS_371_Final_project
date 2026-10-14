from claude_client import ClaudeClient


client = ClaudeClient()

response, usage = client.generate(
    "Reply with exactly: Agent Claude client works.",
    max_tokens=50,
)


print(response)

print("\nUsage:")
print(usage)