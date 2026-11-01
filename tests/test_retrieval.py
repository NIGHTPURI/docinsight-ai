import unittest

from app.services.retrieval_service import retrieve_sources, format_context


class RetrievalTest(unittest.TestCase):
    def test_finds_evidence_after_old_prefix_limit(self):
        text = ("Background general information. " * 700) + "\nCancellation deadline is 45 days."
        sources = retrieve_sources(text, "What is the cancellation deadline?")
        self.assertTrue(sources)
        self.assertTrue(any(s.start_char > 12000 and "45 days" in s.text for s in sources))
        for source in sources:
            self.assertEqual(source.text, text[source.start_char:source.end_char])

    def test_no_overlap_means_no_evidence(self):
        for question in ("quasar", "the is a", "   "):
            self.assertEqual(retrieve_sources("A contract covers delivery.", question), [])

    def test_korean_particles_and_case_are_normalized_only_for_search(self):
        text = "배송비는 무료입니다. 보관 기간은 30일입니다. Python 지원."
        self.assertTrue(retrieve_sources(text, "배송비가 얼마인가요?"))
        sources = retrieve_sources(text, "PYTHON")
        self.assertEqual(sources[0].text, text)

    def test_context_is_bounded_nonoverlapping_and_deterministic(self):
        text = ("contract delivery obligations " * 1000)
        first = retrieve_sources(text, "contract")
        self.assertEqual(first, retrieve_sources(text, "contract"))
        self.assertLessEqual(len(first), 4)
        self.assertLessEqual(sum(len(s.text) for s in first), 4800)
        for i, left in enumerate(first):
            for right in first[i + 1:]:
                self.assertTrue(left.end_char <= right.start_char or right.end_char <= left.start_char)
        for source in first:
            self.assertIn("[" + source.source_id + "]", format_context(first))

    def test_empty_and_unicode_offsets(self):
        self.assertEqual(retrieve_sources("", "contract"), [])
        text = "🙂" * 1500 + " Shipping deadline is Friday."
        sources = retrieve_sources(text, "shipping")
        self.assertTrue(sources)
        for source in sources:
            self.assertEqual(source.text, text[source.start_char:source.end_char])
