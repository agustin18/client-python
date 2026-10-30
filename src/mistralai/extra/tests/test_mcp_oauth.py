"""Tests for MCP OAuth discovery and SSE base URL handling."""

import unittest
from unittest import mock

from mistralai.extra.mcp.auth import build_oauth_params, get_oauth_server_metadata
from mistralai.extra.mcp.sse import MCPClientSSE, SSEServerParams


class TestOAuthServerMetadataFallback(unittest.IsolatedAsyncioTestCase):
    async def test_fallback_sets_registration_endpoint(self) -> None:
        with mock.patch(
            "mistralai.extra.mcp.auth.get_well_known_authorization_server_metadata",
            mock.AsyncMock(return_value=None),
        ):
            metadata = await get_oauth_server_metadata("https://mcp.example")

        self.assertEqual(metadata.registration_endpoint, "https://mcp.example/register")

    async def test_build_oauth_params_uses_fallback_registration_endpoint(self) -> None:
        with (
            mock.patch(
                "mistralai.extra.mcp.auth.get_well_known_authorization_server_metadata",
                mock.AsyncMock(return_value=None),
            ),
            mock.patch(
                "mistralai.extra.mcp.auth.dynamic_client_registration",
                mock.AsyncMock(return_value=("client-id", "client-secret")),
            ) as register,
        ):
            params = await build_oauth_params(
                "https://mcp.example",
                redirect_url="https://app.example/callback",
                async_client=mock.AsyncMock(),
            )

        self.assertEqual(params.client_id, "client-id")
        self.assertEqual(params.client_secret, "client-secret")
        assert register.await_args is not None
        self.assertEqual(register.await_args.kwargs["register_endpoint"], "https://mcp.example/register")


class TestMCPClientSSEBaseUrl(unittest.TestCase):
    def test_base_url_removes_only_sse_suffix(self) -> None:
        cases = {
            "https://mcp.example.services/sse": "https://mcp.example.services",
            "https://example.com/api/messages/sse": "https://example.com/api/messages",
            "https://example.com/mcp/events": "https://example.com/mcp/events",
            "https://mcp.example/sse/": "https://mcp.example",
        }

        for url, expected in cases.items():
            with self.subTest(url=url):
                client = MCPClientSSE(sse_params=SSEServerParams(url=url))

                self.assertEqual(client.base_url, expected)


if __name__ == "__main__":
    unittest.main()
