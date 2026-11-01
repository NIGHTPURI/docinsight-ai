import unittest
from app.upload_limit import UploadLimitMiddleware


class UploadLimitTest(unittest.IsolatedAsyncioTestCase):
    async def execute(self, chunks, headers=(), limit=8):
        called, sent = [], []
        messages = iter({"type": "http.request", "body": body, "more_body": i < len(chunks) - 1}
                        for i, body in enumerate(chunks))
        async def receive():
            return next(messages)
        async def send(message):
            sent.append(message)
        async def downstream(scope, receive, send):
            called.append(await receive())
        await UploadLimitMiddleware(downstream, max_body_bytes=limit)(
            {"type": "http", "method": "POST", "headers": list(headers)}, receive, send)
        return called, sent

    async def test_chunked_body_is_rejected_without_parsing(self):
        called, sent = await self.execute([b"12345", b"6789"])
        self.assertEqual(called, [])
        self.assertEqual(sent[0]["status"], 413)

    async def test_declared_size_is_not_trusted_when_actual_body_is_larger(self):
        called, sent = await self.execute([b"123456789"], [(b"content-length", b"1")])
        self.assertEqual(called, [])
        self.assertEqual(sent[0]["status"], 413)

    async def test_exact_budget_replays_identical_body_once(self):
        called, sent = await self.execute([b"123", b"45678"])
        self.assertEqual(called, [{"type": "http.request", "body": b"12345678", "more_body": False}])
        self.assertEqual(sent, [])

    async def test_declared_overflow_is_rejected_before_reading(self):
        called, sent = await self.execute([], [(b"content-length", b"9")])
        self.assertEqual(called, [])
        self.assertEqual(sent[0]["status"], 413)

    async def test_extreme_content_length_is_rejected_without_integer_conversion(self):
        called, sent = await self.execute([], [(b"content-length", b"9" * 5000)])
        self.assertEqual(called, [])
        self.assertEqual(sent[0]["status"], 413)
