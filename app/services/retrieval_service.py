"""Local lexical retrieval with exact offsets into the stored extracted text.

Scores rank text overlap; they are not confidence or answer correctness scores.
No embeddings, network requests, or extra database schema are needed.
"""
from collections import Counter
from dataclasses import dataclass, asdict
import math
import re
import unicodedata

CHUNK_CHARS = 1200
OVERLAP_CHARS = 200
MAX_SOURCES = 4
TOKEN = re.compile(r"[a-z0-9]+(?:\+\+|#)?|[가-힣]+")
STOP_WORDS = frozenset("a an the is are was were be to of in on for and or what when how does do please this that document 문서 내용 무엇 언제 어떻게 알려 주세요 알려주세요 대한 에서 있는 것은 입니다".split())
KOREAN_SUFFIXES = ("에서는", "으로", "에서", "까지", "부터", "은", "는", "이", "가", "을", "를", "의", "에", "와", "과")


@dataclass(frozen=True)
class SourceExcerpt:
    source_id: str
    start_char: int
    end_char: int
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def _tokens(text: str) -> list[str]:
    result = []
    for token in TOKEN.findall(unicodedata.normalize("NFKC", text).casefold()):
        if token in STOP_WORDS:
            continue
        if re.fullmatch(r"[가-힣]+", token):
            for suffix in KOREAN_SUFFIXES:
                if token.endswith(suffix) and len(token) > len(suffix) + 1:
                    token = token[:-len(suffix)]
                    break
        if token not in STOP_WORDS:
            result.append(token)
    return result


def retrieve_sources(text: str, question: str) -> list[SourceExcerpt]:
    query = set(_tokens(question))
    if not query or not text.strip():
        return []
    chunks = [SourceExcerpt(f"chunk-{start}", start, min(start + CHUNK_CHARS, len(text)),
                            text[start:start + CHUNK_CHARS])
              for start in range(0, len(text), CHUNK_CHARS - OVERLAP_CHARS)]
    frequencies = [Counter(_tokens(chunk.text)) for chunk in chunks]
    document_frequency = Counter(term for freq in frequencies for term in query if term in freq)
    ranked = []
    for chunk, freq in zip(chunks, frequencies):
        score = sum(math.log1p(len(chunks) / document_frequency[term]) * (1 + math.log(freq[term]))
                    for term in query if freq[term])
        if score > 0:
            ranked.append((score, chunk))
    ranked.sort(key=lambda item: (-item[0], item[1].start_char))
    selected = []
    for _, chunk in ranked:
        # Avoid spending the context budget twice on overlapping evidence.
        if any(chunk.start_char < other.end_char and other.start_char < chunk.end_char for other in selected):
            continue
        selected.append(chunk)
        if len(selected) == MAX_SOURCES:
            break
    return selected


def format_context(sources: list[SourceExcerpt]) -> str:
    return "\n\n".join(f"[{source.source_id}]\n{source.text}" for source in sources)
