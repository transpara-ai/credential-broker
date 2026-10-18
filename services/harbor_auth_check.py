"""Check one configured Harbor scope without exposing a credential or token.

The protected GitHub environment supplies the endpoint, repository, and robot
identity. Workflow dispatch chooses only this reviewed operation; it cannot
supply any of those values or change the network destination.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.parse
import urllib.request

REQUESTED_ACTIONS = frozenset({"pull", "push"})
REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)+\Z")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Reject redirects so Basic credentials do not follow a changed endpoint."""

    def redirect_request(self, request, file_pointer, code, message, headers, url):
        return None


def verify(token_url: str, repository: str, username: str, password: str) -> None:
    """Require Harbor's HTTPS reply to grant pull and push for the repository.

    This makes one request with a 20-second timeout and reads at most 64 KiB.
    It inspects a claim from Harbor's TLS response but does not independently
    verify the JWT signature or push an image. Any malformed input or response,
    redirect, missing permission, or network failure raises an exception.
    """

    endpoint = urllib.parse.urlsplit(token_url)
    if (
        endpoint.scheme != "https"
        or not endpoint.hostname
        or endpoint.path != "/service/token"
        or endpoint.username
        or endpoint.password
        or endpoint.query
        or endpoint.fragment
    ):
        raise ValueError("invalid Harbor endpoint")
    if not REPOSITORY_PATTERN.fullmatch(repository) or not username or not password:
        raise ValueError("invalid Harbor configuration")

    scope = f"repository:{repository}:pull,push"
    query = urllib.parse.urlencode({"service": "harbor-registry", "scope": scope})
    authorization = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    request = urllib.request.Request(
        f"{token_url}?{query}",
        headers={"Authorization": f"Basic {authorization}"},
    )
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=20) as response:
        if response.status != 200:
            raise ValueError("Harbor did not issue a token")
        body = response.read(65537)
        if len(body) > 65536:
            raise ValueError("Harbor response exceeded the size limit")
        token = json.loads(body).get("token", "")
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Harbor returned an invalid token")
    claims = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
    if not any(
        entry.get("name") == repository
        and REQUESTED_ACTIONS <= set(entry.get("actions", []))
        for entry in claims.get("access", [])
    ):
        raise ValueError("Harbor token lacks repository pull/push access")


def main() -> int:
    """Report only pass/fail; never write the secret or Harbor token to logs."""

    try:
        verify(
            os.environ.get("HARBOR_TOKEN_URL", ""),
            os.environ.get("HARBOR_REPOSITORY", ""),
            os.environ.get("HARBOR_USERNAME", ""),
            os.environ.get("HARBOR_PASSWORD", ""),
        )
    except Exception:
        print("Harbor authorization check failed", file=sys.stderr)
        return 1
    print("Harbor repository pull/push authorization verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
