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
            "User-Agent": "infrasentry-ai-buffer-publisher/1.0",
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
        messages = "; ".join(
            error.get("message", "Unknown GraphQL error") for error in payload["errors"]
        )
        raise RuntimeError(f"Buffer GraphQL error: {messages}")

    return payload["data"]


def linkedin_channel_id() -> str:
    account_data = graphql(
        """
        query AccountOrganizations {
          account {
            organizations {
              id
            }
          }
        }
        """
    )

    organizations = account_data.get("account", {}).get("organizations", [])
    matches: list[str] = []

    for organization in organizations:
        organization_id = organization["id"]
        channel_data = graphql(
            f'''\n            query OrganizationChannels {{\n              channels(input: {{ organizationId: "{organization_id}" }}) {{\n                id\n                service\n              }}\n            }}\n            '''
        )
        for channel in channel_data.get("channels", []):
            if str(channel.get("service", "")).lower() == "linkedin":
                matches.append(channel["id"])

    if not matches:
        raise RuntimeError("No LinkedIn channel is connected in Buffer")
    if len(matches) > 1:
        raise RuntimeError(
            "Multiple LinkedIn channels are connected. Configure a target channel before publishing."
        )

    return matches[0]


def graphql_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def main() -> int:
    text = os.environ.get("POST_TEXT", "").strip()
    if not text:
        raise RuntimeError("POST_TEXT is empty")

    channel_id = linkedin_channel_id()
    query = f'''\n    mutation PublishLinkedInPost {{\n      createPost(input: {{\n        text: {graphql_string(text)}\n        channelId: "{channel_id}"\n        schedulingType: automatic\n        mode: shareNow\n      }}) {{\n        ... on PostActionSuccess {{\n          post {{\n            id\n            text\n            status\n            sentAt\n          }}\n        }}\n        ... on MutationError {{\n          message\n        }}\n      }}\n    }}\n    '''

    data = graphql(query)
    result = data.get("createPost") or {}

    if result.get("message"):
        raise RuntimeError(f"Buffer rejected the post: {result['message']}")

    post = result.get("post")
    if not post:
        raise RuntimeError(f"Unexpected Buffer response: {json.dumps(result)}")

    print(
        "Buffer LinkedIn post accepted for immediate publication: "
        f"id={post['id']} status={post.get('status')} sent_at={post.get('sentAt')}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
