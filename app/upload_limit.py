"""Bound request bytes before Starlette parses or spools multipart files."""
from starlette.responses import JSONResponse


class UploadLimitMiddleware:
    def __init__(self, app, *, max_body_bytes: int):
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return
        response = JSONResponse({"detail": "요청 크기가 업로드 한도를 초과했습니다."}, status_code=413)
        for key, value in scope.get("headers", []):
            if key.lower() == b"content-length" and value.isdigit():
                # Compare decimal bytes, avoiding huge integer conversion on hostile headers.
                declared = value.lstrip(b"0") or b"0"
                limit = str(self.max_body_bytes).encode("ascii")
                if len(declared) > len(limit) or (len(declared) == len(limit) and declared > limit):
                    await response(scope, receive, send)
                    return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            data = message.get("body", b"")
            if len(body) + len(data) > self.max_body_bytes:
                await response(scope, receive, send)
                return
            body.extend(data)
            if not message.get("more_body", False):
                break
        replayed = False

        async def replay():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)
