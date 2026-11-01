from support import settings
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import httpx
from fastapi import HTTPException
from openai import APITimeoutError, APIConnectionError
from app.services import ai_service


class AiBoundaryTest(unittest.TestCase):
    def test_missing_key_does_not_construct_a_client(self):
        with patch.object(settings, "openai_api_key", ""), patch.object(ai_service, "OpenAI") as sdk:
            with self.assertRaises(HTTPException) as error:
                ai_service.summarize_document("text")
        self.assertEqual(error.exception.status_code, 503)
        sdk.assert_not_called()

    def test_one_attempt_has_limits_and_closes_client(self):
        with patch.object(settings, "openai_api_key", "unit-test-only"), patch.object(ai_service, "OpenAI") as sdk:
            client = sdk.return_value.__enter__.return_value
            client.chat.completions.create.return_value = SimpleNamespace(choices=[
                SimpleNamespace(message=SimpleNamespace(content=" answer "), finish_reason="stop")])
            self.assertEqual(ai_service.answer_question_about_document("[chunk-0] evidence", "question"), "answer")
            sdk.assert_called_once_with(api_key="unit-test-only", timeout=30.0, max_retries=0)
            client.chat.completions.create.assert_called_once()
            self.assertEqual(client.chat.completions.create.call_args.kwargs["max_completion_tokens"], 1000)
            sdk.return_value.__exit__.assert_called_once()

    def test_empty_or_incomplete_results_are_not_success(self):
        for content, reason in ((None, "stop"), ("  ", "stop"), ("partial", "length"), ("refused", "content_filter")):
            with self.subTest(content=content, reason=reason), patch.object(settings, "openai_api_key", "unit-test-only"), patch.object(ai_service, "OpenAI") as sdk:
                client = sdk.return_value.__enter__.return_value
                client.chat.completions.create.return_value = SimpleNamespace(choices=[
                    SimpleNamespace(message=SimpleNamespace(content=content), finish_reason=reason)])
                with self.assertRaises(HTTPException) as error:
                    ai_service.summarize_document("text")
                self.assertEqual(error.exception.status_code, 502)

    def test_transport_errors_are_sanitized_and_not_retried(self):
        request = httpx.Request("POST", "https://example.invalid")
        for failure, status in ((APITimeoutError(request=request), 504),
                                (APIConnectionError(message="private-provider-detail", request=request), 502)):
            with self.subTest(status=status), patch.object(settings, "openai_api_key", "unit-test-only"), patch.object(ai_service, "OpenAI") as sdk:
                sdk.return_value.__enter__.return_value.chat.completions.create.side_effect = failure
                with self.assertRaises(HTTPException) as error:
                    ai_service.summarize_document("text")
                self.assertEqual(error.exception.status_code, status)
                self.assertNotIn("private-provider-detail", error.exception.detail)
                sdk.return_value.__enter__.return_value.chat.completions.create.assert_called_once()

    def test_summary_limits_input_explicitly(self):
        with patch.object(ai_service, "_complete", return_value="summary") as complete:
            ai_service.summarize_document("a" * 12000 + "SHOULD_NOT_BE_SENT")
        self.assertNotIn("SHOULD_NOT_BE_SENT", complete.call_args.args[1])
