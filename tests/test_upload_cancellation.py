from support import settings
import asyncio
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from starlette.datastructures import Headers, UploadFile
from app.routers.documents import upload_document


class UploadCancellationTest(unittest.IsolatedAsyncioTestCase):
    async def test_cancelled_extraction_rolls_back_and_removes_file(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(settings, "upload_dir", directory):
            upload = UploadFile(io.BytesIO(b"fake-pdf"), filename="sample.pdf",
                                headers=Headers({"content-type": "application/pdf"}))
            db = Mock()
            with patch("app.routers.documents.run_in_threadpool", new=AsyncMock(side_effect=asyncio.CancelledError)), \
                    patch("app.routers.documents.create_document") as persist:
                with self.assertRaises(asyncio.CancelledError):
                    await upload_document(upload, db)
            await upload.close()
            db.rollback.assert_called_once()
            persist.assert_not_called()
            self.assertEqual(list(Path(directory).iterdir()), [])
