from support import settings
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import Document, QuestionAnswer


def pdf_bytes(pages):
    with fitz.open() as pdf:
        for text in pages:
            pdf.new_page().insert_text((72, 72), text)
        return pdf.tobytes()


class DocumentApiTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        upload = patch.object(settings, "upload_dir", self.directory.name)
        upload.start()
        self.addCleanup(upload.stop)
        blocker = patch("app.services.ai_service.OpenAI", side_effect=AssertionError("Live API forbidden in tests"))
        blocker.start()
        self.addCleanup(blocker.stop)
        Base.metadata.drop_all(engine)
        self.client = TestClient(app, raise_server_exceptions=False)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def upload(self, pages=None, name="sample.pdf", body=None):
        return self.client.post("/documents/upload", files={
            "file": (name, body if body is not None else pdf_bytes(pages or ["Shipping deadline is Friday."]), "application/pdf")
        })

    def counts(self):
        with SessionLocal() as db:
            return db.query(Document).count(), db.query(QuestionAnswer).count()

    def test_keyless_startup_upload_list_and_detail(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        uploaded = self.upload()
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        document_id = uploaded.json()["document_id"]
        self.assertEqual(len(self.client.get("/documents").json()), 1)
        detail = self.client.get(f"/documents/{document_id}").json()
        self.assertGreater(detail["extracted_text_length"], 0)
        self.assertEqual(self.counts(), (1, 0))

    def test_filename_never_controls_disk_path(self):
        response = self.upload(name="../../escape.pdf")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["filename"], "escape.pdf")
        with SessionLocal() as db:
            path = Path(db.query(Document).one().original_path)
            self.assertEqual(path.parent, Path(self.directory.name))
            self.assertNotIn("escape", path.name)

    def test_invalid_and_textless_pdf_are_rejected_and_removed(self):
        for data in (b"not a PDF", pdf_bytes([""])):
            with self.subTest(size=len(data)):
                self.assertEqual(self.upload(body=data).status_code, 400)
                self.assertEqual(list(Path(self.directory.name).iterdir()), [])
                self.assertEqual(self.counts(), (0, 0))

    def test_oversized_pdf_is_rejected_and_partial_file_removed(self):
        with patch.object(settings, "max_upload_bytes", 32):
            response = self.upload()
        self.assertEqual(response.status_code, 413)
        self.assertEqual(list(Path(self.directory.name).iterdir()), [])
        self.assertEqual(self.counts(), (0, 0))

    def test_page_and_text_budgets_do_not_save_a_document(self):
        with patch.object(settings, "max_pdf_pages", 1):
            self.assertEqual(self.upload(pages=["one", "two"]).status_code, 413)
        with patch.object(settings, "max_document_chars", 5):
            self.assertEqual(self.upload().status_code, 413)
        self.assertEqual(self.counts(), (0, 0))
        self.assertEqual(list(Path(self.directory.name).iterdir()), [])

    def test_file_size_exact_boundary_and_one_byte_over(self):
        body = pdf_bytes(["Boundary example."])
        with patch.object(settings, "max_upload_bytes", len(body)):
            self.assertEqual(self.upload(body=body).status_code, 200)
            self.assertEqual(self.upload(body=body + b" ").status_code, 413)
        self.assertEqual(self.counts(), (1, 0))
        self.assertEqual(len(list(Path(self.directory.name).iterdir())), 1)

    def test_preparse_limit_keeps_cors_headers(self):
        response = self.client.post("/documents/upload",
                                    content=b"x" * (settings.max_upload_bytes + 64 * 1024 + 1),
                                    headers={"Origin": "http://127.0.0.1:5173"})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://127.0.0.1:5173")
        self.assertEqual(list(Path(self.directory.name).iterdir()), [])

    def test_database_failure_removes_uploaded_file(self):
        with patch("app.routers.documents.create_document", side_effect=RuntimeError("injected storage failure")):
            self.assertEqual(self.upload().status_code, 500)
        self.assertEqual(list(Path(self.directory.name).iterdir()), [])
        self.assertEqual(self.counts(), (0, 0))

    def test_long_document_search_and_qa_include_late_evidence(self):
        pages = ["Background overview text for this document.\n" * 20] * 25
        pages += ["Cancellation deadline is 45 days."]
        response = self.upload(pages=pages)
        self.assertEqual(response.status_code, 200, response.text)
        document_id = response.json()["document_id"]
        query = {"question": "What is the cancellation deadline?"}
        found = self.client.post(f"/documents/{document_id}/search", json=query)
        self.assertEqual(found.status_code, 200, found.text)
        sources = found.json()["sources"]
        self.assertTrue(any(source["start_char"] > 12000 and "45 days" in source["text"] for source in sources))
        with patch("app.routers.documents.answer_question_about_document", return_value="45 days") as answer:
            response = self.client.post(f"/documents/{document_id}/ask", json=query)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("45 days", answer.call_args.args[0])
        self.assertLess(len(answer.call_args.args[0]), 5000)
        self.assertEqual(response.json()["sources"], sources)
        self.assertEqual(self.counts(), (1, 1))
        self.assertEqual(len(self.client.get(f"/documents/{document_id}/questions").json()), 1)

    def test_no_matching_evidence_skips_ai_and_explains_search_limit(self):
        document_id = self.upload().json()["document_id"]
        with patch("app.routers.documents.answer_question_about_document", side_effect=AssertionError("Must not call AI")):
            response = self.client.post(f"/documents/{document_id}/ask", json={"question": "quasar"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["sources"], [])
        self.assertEqual(response.json()["answer_status"], "no_evidence")

    def test_missing_key_or_provider_failure_does_not_save_an_answer(self):
        document_id = self.upload().json()["document_id"]
        self.assertEqual(self.client.post(f"/documents/{document_id}/ask", json={"question": "shipping"}).status_code, 503)
        with patch("app.routers.documents.answer_question_about_document", side_effect=HTTPException(504, "timeout")):
            self.assertEqual(self.client.post(f"/documents/{document_id}/ask", json={"question": "shipping"}).status_code, 504)
        self.assertEqual(self.counts(), (1, 0))

    def test_question_validation_and_missing_document(self):
        document_id = self.upload().json()["document_id"]
        for question in ("", "  ", "a" * 1001):
            self.assertEqual(self.client.post(f"/documents/{document_id}/ask", json={"question": question}).status_code, 422)
        for action in ("ask", "search"):
            self.assertEqual(self.client.post(f"/documents/999/{action}", json={"question": "shipping"}).status_code, 404)

    def test_summary_is_cached_and_reports_prefix_coverage(self):
        document_id = self.upload(pages=["Background overview.\n" * 20] * 40).json()["document_id"]
        with patch("app.routers.documents.summarize_document", return_value="A prefix summary.") as summarize:
            first = self.client.post(f"/documents/{document_id}/summarize")
            second = self.client.post(f"/documents/{document_id}/summarize")
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json(), second.json())
        self.assertTrue(first.json()["truncated"])
        self.assertEqual(first.json()["source_chars"], 12000)
        summarize.assert_called_once()

    def test_rejected_browser_origin_has_no_allow_origin_header(self):
        response = self.client.get("/documents", headers={"origin": "https://unrelated.example"})
        self.assertNotIn("access-control-allow-origin", response.headers)
