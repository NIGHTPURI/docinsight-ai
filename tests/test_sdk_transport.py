from support import settings
import json
import unittest
from unittest.mock import patch
import httpx
from fastapi import HTTPException
from openai import OpenAI as RealOpenAI
from app.services import ai_service


class SdkTransportTest(unittest.TestCase):
    """Exercise the installed SDK's real serialization/parsing without a network transport."""

    def invoke(self, handler):
        requests = []
        def transport(request):
            requests.append(request)
            return handler(request)
        client = RealOpenAI(api_key="offline-test-only", max_retries=0, timeout=30,
                            http_client=httpx.Client(transport=httpx.MockTransport(transport)))
        with patch.object(settings, "openai_api_key", "offline-test-only"), \
                patch.object(ai_service, "OpenAI", return_value=client):
            try:
                result = ai_service.answer_question_about_document("[chunk-13000]\nNotice is 45 days.", "Notice period?")
            except HTTPException as error:
                result = error
        self.assertTrue(client.is_closed())
        self.assertEqual(len(requests), 1)
        return result, requests[0]

    @staticmethod
    def completion(reason="stop"):
        return httpx.Response(200, json={
            "id": "offline-completion", "object": "chat.completion", "created": 1,
            "model": "offline-model", "choices": [{"index": 0, "finish_reason": reason,
            "message": {"role": "assistant", "content": "45 days [chunk-13000]"}}]})

    def test_actual_sdk_serializes_bounded_messages_and_parses_answer(self):
        result, request = self.invoke(lambda _: self.completion())
        self.assertEqual(result, "45 days [chunk-13000]")
        self.assertEqual(request.url.path, "/v1/chat/completions")
        body = json.loads(request.content)
        self.assertEqual(body["max_completion_tokens"], 1000)
        self.assertEqual(body["model"], settings.model_name)
        self.assertIn("[chunk-13000]", body["messages"][1]["content"])
        self.assertEqual(len(body["messages"]), 2)

    def test_actual_sdk_truncated_response_is_rejected(self):
        result, _ = self.invoke(lambda _: self.completion("length"))
        self.assertEqual(result.status_code, 502)

    def test_actual_sdk_server_error_is_not_retried_or_exposed(self):
        result, _ = self.invoke(lambda _: httpx.Response(500, json={"error": {"message": "private-provider-detail"}}))
        self.assertEqual(result.status_code, 502)
        self.assertNotIn("private-provider-detail", result.detail)

    def test_actual_sdk_read_timeout_is_mapped_without_retry(self):
        def timeout(request):
            raise httpx.ReadTimeout("private-timeout-detail", request=request)
        result, _ = self.invoke(timeout)
        self.assertEqual(result.status_code, 504)
