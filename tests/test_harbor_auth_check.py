"""Check the public broker contract with fabricated credentials and replies."""

from __future__ import annotations

import base64
import contextlib
import importlib.util
import io
import json
import os
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "services" / "harbor_auth_check.py"
WORKFLOW = ROOT / ".github" / "workflows" / "credential-broker.yml"
VERIFY_WORKFLOW = ROOT / ".github" / "workflows" / "verify.yml"
spec = importlib.util.spec_from_file_location("harbor_auth_check", SCRIPT)
broker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(broker)
TOKEN_URL = "https://harbor.example.invalid/service/token"
REPOSITORY = "example/image"


class FakeResponse(io.BytesIO):
    """Return a fake Harbor JSON body without network access or real secrets."""

    status = 200


def token_with(actions: list[str]) -> bytes:
    """Build an unsigned test token; production inspects Harbor's TLS reply."""

    claims = {"access": [{"name": REPOSITORY, "actions": actions}]}
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return json.dumps({"token": f"header.{payload}.signature"}).encode()


class HarborAuthCheckTests(unittest.TestCase):
    def test_requests_fixed_scope_without_redirects(self) -> None:
        opener = mock.Mock()
        opener.open.return_value = FakeResponse(token_with(["pull", "push"]))
        with mock.patch.object(broker.urllib.request, "build_opener", return_value=opener) as build:
            broker.verify(TOKEN_URL, REPOSITORY, "test-user", "test-password")
        self.assertIsInstance(build.call_args.args[0], broker.NoRedirect)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url.split("?")[0], TOKEN_URL)
        self.assertIn("example%2Fimage", request.full_url)
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 20)

    def test_rejects_missing_push(self) -> None:
        opener = mock.Mock()
        opener.open.return_value = FakeResponse(token_with(["pull"]))
        with mock.patch.object(broker.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(ValueError):
                broker.verify(TOKEN_URL, REPOSITORY, "test-user", "test-password")

    def test_rejects_oversized_response(self) -> None:
        opener = mock.Mock()
        opener.open.return_value = FakeResponse(b"x" * 65537)
        with mock.patch.object(broker.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(ValueError):
                broker.verify(TOKEN_URL, REPOSITORY, "test-user", "test-password")

    def test_rejects_redirect_to_another_host(self) -> None:
        self.assertIsNone(broker.NoRedirect().redirect_request(None, None, 302, None, None, "https://other.invalid"))

    def test_rejects_untrusted_configuration(self) -> None:
        for url, repository in (
            ("http://harbor.example.invalid/service/token", REPOSITORY),
            ("https://user@harbor.example.invalid/service/token", REPOSITORY),
            ("https://harbor.example.invalid/service/token?x=1", REPOSITORY),
            (TOKEN_URL, "image:pull,push"),
        ):
            with self.subTest(url=url, repository=repository), self.assertRaises(ValueError):
                broker.verify(url, repository, "test-user", "test-password")

    def test_failure_output_never_contains_credential(self) -> None:
        output = io.StringIO()
        with (
            mock.patch.dict(os.environ, {"HARBOR_PASSWORD": "test-password"}),
            mock.patch.object(broker, "verify", side_effect=ValueError("test-password")),
            contextlib.redirect_stderr(output),
        ):
            self.assertEqual(broker.main(), 1)
        self.assertEqual(output.getvalue().strip(), "Harbor authorization check failed")

    def test_workflow_uses_only_fixed_dispatch_and_environment_secrets(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("repository_dispatch:", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("environment: credential-broker", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("run: python3 services/harbor_auth_check.py", workflow)
        for name in ("HARBOR_TOKEN_URL", "HARBOR_REPOSITORY", "HARBOR_USERNAME", "HARBOR_PASSWORD"):
            self.assertIn(f"${{{{ secrets.{name} }}}}", workflow)
        self.assertNotIn("${{ inputs.operation }}", workflow)

    def test_pull_request_verification_never_requests_secrets(self) -> None:
        workflow = VERIFY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pull_request:", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("environment:", workflow)
        self.assertNotIn("${{ secrets.", workflow)


if __name__ == "__main__":
    unittest.main()
