from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BUFFER_ENDPOINT = "https://api.buffer.com"


def graphql(query: str) -> dict:
    api_key = os.environ.get("BUFFER_API_KEY")
    if not api_key:
        raise RuntimeError("BUFFER_API_KEY is not configured")

    request = urllib.request.Request(
        BUFFER_ENDPOINT,
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "infrasentry-ai-buffer-smoke-test/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Buffer API HTTP error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Buffer API connection failed: {exc.reason}") from exc

    if payload.get("errors"):
        messages = "; ".join(error.get("message", "Unknown GraphQL error") for error in payload["errors"])
        raise RuntimeError(f"Buffer GraphQL error: {messages}")

    return payload["data"]


def main() -> int:
    account_data = graphql(
        """
        query AccountOrganizations {
          account {
            organizations {
              id
              name
            }
          }
        }
        """
    )

    organizations = account_data.get("account", {}).get("organizations", [])
    if not organizations:
        raise RuntimeError("No Buffer organization was returned for this API key")

    linkedin_channels: list[dict] = []
    for organization in organizations:
        organization_id = organization["id"]
        channel_data = graphql(
            f'''\n            query OrganizationChannels {{\n              channels(input: {{ organizationId: "{organization_id}" }}) {{\n                id\n                name\n                displayName\n                service\n                isQueuePaused\n              }}\n            }}\n            '''
        )
        for channel in channel_data.get("channels", []):
            if str(channel.get("service", "")).lower() == "linkedin":
                linkedin_channels.append(channel)

    if not linkedin_channels:
        raise RuntimeError("Buffer authentication works, but no LinkedIn channel is connected")

    print(f"Buffer authentication OK. LinkedIn channel(s) found: {len(linkedin_channels)}")
    for channel in linkedin_channels:
        print(
            "- "
            f"{channel.get('displayName') or channel.get('name') or 'LinkedIn'} "
            f"(id={channel['id']}, queue_paused={channel.get('isQueuePaused')})"
        )

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output and len(linkedin_channels) == 1:
        with open(github_output, "a", encoding="utf-8") as output:
            output.write(f"linkedin_channel_id={linkedin_channels[0]['id']}\n")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
