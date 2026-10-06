"""Offline checks of consumer semantics and the bounded fetch boundary; no live requests."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/consumer"))
import consume
import fetch_manifest as network

ORIGIN = "https://consumer-demo.example"
NOW = consume.timestamp("2026-10-06T18:00:00Z")
FIXTURES = ROOT / "examples/consumer"


class ConsumerTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((FIXTURES / "manifest.json").read_text())
        self.status = (FIXTURES / "operational-status.json").read_bytes()

    def inspect(self, manifest=None, status=None, omit_status=False):
        return consume.inspect(json.dumps(manifest or self.manifest).encode(),
                               None if omit_status else (status or self.status), ORIGIN, NOW)

    def test_worked_example_is_unverified_manual_review_not_access(self):
        result = self.inspect()
        self.assertEqual(result["manifest"]["state"], "fresh")
        self.assertEqual(result["status_evidence"]["digest"], "matched")
        self.assertEqual(result["status_evidence"]["state"], "unverified")
        self.assertEqual(result["policy"]["decision"], "manual_review")
        self.assertFalse(result["policy"]["access_granted"])
        self.assertIn("claims_not_independently_verified", result["policy"]["reasons"])

    def test_stale_manifest_fixture_is_held(self):
        raw = (FIXTURES / "stale-manifest.json").read_bytes()
        result = consume.inspect(raw, self.status, ORIGIN, NOW)
        self.assertEqual(result["manifest"]["state"], "stale")
        self.assertEqual(result["policy"]["decision"], "hold")

    def test_tampered_bytes_are_rejected(self):
        result = self.inspect(status=(FIXTURES / "tampered-status.json").read_bytes())
        self.assertEqual(result["status_evidence"]["digest"], "mismatch")
        self.assertEqual(result["policy"]["decision"], "hold")

    def test_missing_status_is_explicit(self):
        result = self.inspect(omit_status=True)
        self.assertEqual(result["status_evidence"]["state"], "missing")
        self.assertEqual(result["policy"]["decision"], "hold")

    def test_missing_reference_is_explicit(self):
        del self.manifest["governance_artifacts"]
        self.assertEqual(self.inspect()["status_evidence"]["reason"], "status_reference_missing")

    def test_expiry_boundary_future_and_invalid_timestamps(self):
        for field, value, state in [
            ("expires_at", "2026-10-06T18:00:00Z", "stale"),
            ("published_at", "2026-10-06T18:01:00Z", "invalid"),
            ("expires_at", "not-a-timestamp", "invalid"),
            ("expires_at", "2026-10-06T17:00:00Z", "invalid"),
        ]:
            with self.subTest(field=field, value=value):
                manifest = copy.deepcopy(self.manifest)
                manifest[field] = value
                self.assertEqual(self.inspect(manifest)["manifest"]["state"], state)

    def test_invalid_manifest_schema(self):
        del self.manifest["interaction_profile"]["explicit_invocation_required"]
        self.assertEqual(self.inspect()["policy"]["reasons"], ["manifest_schema_invalid"])

    def test_invalid_offsets_unknown_offset_and_excess_precision_are_held(self):
        for value in ["2026-10-06T19:00:00+00:99", "2026-10-06T19:00:00-00:00",
                      "2026-10-06T19:00:00.1234567Z"]:
            with self.subTest(value=value):
                manifest = copy.deepcopy(self.manifest)
                manifest["expires_at"] = value
                self.assertEqual(self.inspect(manifest)["manifest"]["state"], "invalid")

    def test_other_version_and_wrong_origin_held(self):
        for field, value, code in [
            ("atm_version", "0.1.0", "unsupported_atm_version"),
            ("issuer", {"name": "Fictional", "uri": "https://other.example",
                        "domain": "other.example"}, "issuer_origin_mismatch"),
        ]:
            with self.subTest(field=field):
                manifest = copy.deepcopy(self.manifest)
                manifest[field] = value
                self.assertEqual(self.inspect(manifest)["policy"]["reasons"], [code])

    def test_unsafe_links_and_unsupported_scope_not_followed(self):
        for field, value in [
            ("uri", "https://127.0.0.1/private"),
            ("uri", ORIGIN + "/.well-known/operational-status.json?credential=fictional"),
            ("schema_uri", "https://other.example/schema.json"),
            ("version", "unrecognized-version"),
            ("scope", {"level": "tenant", "identifier": "fictional-tenant"}),
            ("scope", {"level": "surface", "identifier": "fictional-surface"}),
        ]:
            with self.subTest(field=field, value=value), patch.object(
                    consume.subprocess, "run", side_effect=AssertionError("No network allowed")):
                manifest = copy.deepcopy(self.manifest)
                manifest["governance_artifacts"][0][field] = value
                result = self.inspect(manifest)
                self.assertEqual(result["status_evidence"]["state"], "invalid")
                self.assertNotIn("credential=fictional", json.dumps(result))

    def test_ambiguous_references_held(self):
        self.manifest["governance_artifacts"].append(copy.deepcopy(self.manifest["governance_artifacts"][0]))
        self.assertEqual(self.inspect()["status_evidence"]["reason"], "ambiguous_status_references")

    def test_reference_expiry_and_missing_metadata(self):
        ref = self.manifest["governance_artifacts"][0]
        ref["expires_at"] = "2026-10-06T18:00:00Z"
        self.assertEqual(self.inspect()["status_evidence"]["state"], "stale")
        del ref["expires_at"]
        self.assertEqual(self.inspect()["status_evidence"]["state"], "missing")

    def test_claimed_revocation_is_not_accepted_as_verified(self):
        self.manifest["governance_artifacts"][0]["revocation_status"] = "revoked"
        result = self.inspect()
        self.assertEqual(result["policy"]["decision"], "hold")
        self.assertFalse(result["status_evidence"]["revocation_checked"])

    def test_rehashing_tampered_content_does_not_authenticate(self):
        self.status = (FIXTURES / "tampered-status.json").read_bytes()
        self.manifest["governance_artifacts"][0]["hash"] = "sha256:" + hashlib.sha256(self.status).hexdigest()
        result = self.inspect()
        self.assertEqual(result["status_evidence"]["digest"], "matched")
        self.assertEqual(result["status_evidence"]["authentication"], "unverified")
        self.assertEqual(result["policy"]["decision"], "hold")

    def test_changing_both_manifest_and_operational_bytes_still_grants_no_access(self):
        status = json.loads(self.status)
        status["issuer"]["name"] = "Another Fictional Name"
        self.status = json.dumps(status).encode()
        self.manifest["governance_artifacts"][0]["hash"] = "sha256:" + hashlib.sha256(self.status).hexdigest()
        result = self.inspect()
        self.assertEqual(result["status_evidence"]["digest"], "matched")
        self.assertEqual(result["policy"]["decision"], "manual_review")
        self.assertFalse(result["policy"]["access_granted"])
        self.assertEqual(result["manifest"]["authentication"], "unverified")

    def test_status_schema_scope_and_freshness(self):
        for update, state, code in [
            ({"overall_status": "made_up"}, "invalid", "status_schema_invalid"),
            ({"expires_at": "2026-10-06T18:00:00Z"}, "stale", "status_freshness_stale"),
            ({"subject": {"id": "https://other.example"}}, "invalid", "unsupported_status_scope"),
            ({"feed_version": "unrecognized-version"}, "invalid", "unsupported_status_version"),
        ]:
            with self.subTest(update=update):
                status = json.loads(self.status)
                status.update(update)
                raw = json.dumps(status).encode()
                manifest = copy.deepcopy(self.manifest)
                manifest["governance_artifacts"][0]["hash"] = "sha256:" + hashlib.sha256(raw).hexdigest()
                result = self.inspect(manifest, raw)
                self.assertEqual(result["status_evidence"]["state"], state)
                self.assertEqual(result["status_evidence"]["reason"], code)

    def test_unfavorable_declarations_held(self):
        self.manifest["interaction_profile"]["content_triggered_execution"] = True
        self.assertIn("content_execution_not_excluded", self.inspect()["policy"]["reasons"])

    def test_malformed_digest_rejected(self):
        self.manifest["governance_artifacts"][0]["hash"] = "sha256:placeholder"
        self.assertEqual(self.inspect()["status_evidence"]["reason"], "declared_digest_invalid")

    def test_duplicate_nonfinite_large_and_deep_json_rejected(self):
        for raw in [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b'x' * (network.MAX_BYTES + 1),
                    (('{"a":' * 20) + '0' + ('}' * 20)).encode()]:
            with self.subTest(raw_length=len(raw)), self.assertRaises(consume.ConsumerError):
                consume.decode_document(raw)

    def test_cli_offline_example_and_missing_status_file(self):
        args = ["--manifest", str(FIXTURES / "manifest.json"), "--expected-origin", ORIGIN,
                "--at", "2026-10-06T18:00:00Z"]
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = consume.main(args + ["--status-file", str(FIXTURES / "operational-status.json")])
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(output.getvalue())["policy"]["access_granted"])
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()) as output:
            code = consume.main(args + ["--status-file", str(Path(directory) / "absent.json")])
        result = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(result["manifest"]["state"], "fresh")
        self.assertEqual(result["status_evidence"]["state"], "missing")

    def test_network_clock_override_rejected_before_fetch(self):
        with patch.object(consume, "fetch_manifest", side_effect=AssertionError()), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            code = consume.main(["--origin", ORIGIN, "--at", "2026-10-06T18:00:00Z"])
        self.assertEqual(code, 1)
        self.assertIn("offline_option_in_network_mode", output.getvalue())

    def test_fetch_timeout_and_unsanitized_worker_errors(self):
        with patch.object(consume.subprocess, "run", side_effect=subprocess.TimeoutExpired("worker", 8)):
            with self.assertRaisesRegex(consume.ConsumerError, "^fetch_timeout$"):
                consume.fetch_manifest(ORIGIN)
        run = subprocess.CompletedProcess([], 1, b"", b"fictional_sensitive_detail")
        with patch.object(consume.subprocess, "run", return_value=run):
            with self.assertRaisesRegex(consume.ConsumerError, "^fetch_failed$"):
                consume.fetch_manifest(ORIGIN)


class Response:
    def __init__(self, body=b'{}', status=200, headers=None):
        self.body, self.status = body, status
        self.headers = headers or [("Content-Type", "application/json")]

    def getheaders(self):
        return self.headers

    def getheader(self, name, default=None):
        return next((v for k, v in self.headers if k.lower() == name.lower()), default)

    def read(self, count):
        return self.body[:count]


class FetchBoundaryTests(unittest.TestCase):
    def test_transition_and_shared_addresses_are_not_supported(self):
        for address in ["100.64.0.1", "::ffff:10.0.0.1", "2002:0a00:0001::",
                        "2001:0000:4136:e378:8000:63bf:3fff:fdd2"]:
            with self.subTest(address=address):
                self.assertFalse(network.public_address(address))
        self.assertTrue(network.public_address("8.8.8.8"))
        self.assertTrue(network.public_address("2606:4700:4700::1111"))

    def test_origin_parser_rejects_credentials_paths_ports_and_private_literals(self):
        for origin in ["http://demo.example", "https://user:fictional@demo.example",
                       "https://demo.example/path", "https://demo.example:8443",
                       "https://demo.example?q=fictional", "https://demo.example#fragment",
                       "https://127.0.0.1", "https://10.0.0.1", "https://[::1]",
                       "https://demo.example\n", "https://demo..example", "https://localhost"]:
            with self.subTest(origin=origin), self.assertRaises(network.FetchError):
                network.normalize_origin(origin)

    def test_nonpublic_and_mixed_dns_answers_rejected_before_connection(self):
        def answer(ip):
            return (socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443))
        for addresses in [["127.0.0.1"], ["169.254.169.254"], ["224.0.0.1"],
                          ["8.8.8.8", "10.0.0.1"], []]:
            with self.subTest(addresses=addresses):
                connection = Mock(side_effect=AssertionError("must not connect"))
                with self.assertRaises(network.FetchError):
                    network.fetch(ORIGIN, resolver=Mock(return_value=[answer(x) for x in addresses]),
                                  connection=connection)
                connection.assert_not_called()

    def test_public_endpoint_is_pinned_and_request_has_no_credentials(self):
        endpoint = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))
        resolver = Mock(return_value=[endpoint])
        client = Mock()
        client.getresponse.return_value = Response()
        connection = Mock(return_value=client)
        self.assertEqual(network.fetch(ORIGIN, resolver, connection), b'{}')
        resolver.assert_called_once_with("consumer-demo.example", 443, type=socket.SOCK_STREAM)
        connection.assert_called_once_with("consumer-demo.example", endpoint)
        args, kwargs = client.request.call_args
        self.assertEqual(args, ("GET", "/.well-known/agent-trust.json"))
        self.assertNotIn("Authorization", kwargs["headers"])
        self.assertNotIn("Cookie", kwargs["headers"])
        client.close.assert_called_once()

    def test_pinned_connection_keeps_original_tls_hostname_without_second_dns(self):
        endpoint = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))
        raw = Mock()
        raw.getpeername.return_value = ("8.8.8.8", 443)
        context = Mock()
        with patch.object(network.ssl, "create_default_context", return_value=context), \
                patch.object(network.socket, "socket", return_value=raw), \
                patch.object(network.socket, "getaddrinfo", side_effect=AssertionError("no re-resolution")):
            client = network.PinnedHTTPSConnection("consumer-demo.example", endpoint)
            client.connect()
        raw.connect.assert_called_once_with(("8.8.8.8", 443))
        context.wrap_socket.assert_called_once_with(raw, server_hostname="consumer-demo.example")

    def test_real_default_tls_context_checks_certificates_and_hostnames(self):
        endpoint = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))
        client = network.PinnedHTTPSConnection("consumer-demo.example", endpoint)
        self.assertEqual(client._context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(client._context.check_hostname)

    def test_peer_address_must_match_the_pinned_address(self):
        endpoint = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))
        raw = Mock()
        raw.getpeername.return_value = ("1.1.1.1", 443)
        with patch.object(network.socket, "socket", return_value=raw):
            client = network.PinnedHTTPSConnection("consumer-demo.example", endpoint)
            with self.assertRaisesRegex(network.FetchError, "unsafe_address"):
                client.connect()
        raw.close.assert_called_once()

    def test_worker_rejects_private_origin_without_a_request(self):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "tools/consumer/fetch_manifest.py"),
                                 "https://127.0.0.1"], capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.stderr.strip(), b"invalid_origin")

    def test_redirects_encodings_lengths_and_oversize_rejected(self):
        scenarios = [
            Response(status=302), Response(headers=[("Content-Type", "text/html")]),
            Response(headers=[("Content-Type", "application/json"), ("Content-Encoding", "gzip")]),
            Response(headers=[("Content-Type", "application/json"), ("Content-Length", "65537")]),
            Response(headers=[("Content-Type", "application/json"), ("Content-Length", "2"),
                              ("Content-Length", "2")]),
            Response(headers=[("Content-Type", "application/json"), ("Content-Length", "2"),
                              ("Transfer-Encoding", "chunked")]),
            Response(body=b'x' * (network.MAX_BYTES + 1)),
        ]
        endpoint = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))
        for response in scenarios:
            with self.subTest(status=response.status, headers=response.headers):
                client = Mock()
                client.getresponse.return_value = response
                with self.assertRaises(network.FetchError):
                    network.fetch(ORIGIN, Mock(return_value=[endpoint]), Mock(return_value=client))
                self.assertEqual(client.request.call_count, 1)
                client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
