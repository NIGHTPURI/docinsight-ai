import { useEffect, useState } from "react";
import "./App.css";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function responseError(res, fallback) {
  const data = await res.json().catch(() => null);
  return new Error(typeof data?.detail === "string" ? data.detail : fallback);
}

export default function App() {
  const [file, setFile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [summary, setSummary] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const res = await fetch(`${API}/documents`);
        if (!res.ok) {
          throw new Error("문서 목록을 불러오지 못했습니다.");
        }

        const data = await res.json();
        setDocuments(data);
      } catch (error) {
        console.error(error);
        setErrorMessage("문서 목록을 불러오는 중 오류가 발생했습니다.");
      }
    };

    loadDocuments();
  }, []);

  const fetchDocuments = async () => {
    const res = await fetch(`${API}/documents`);
    if (!res.ok) {
      throw new Error("문서 목록을 불러오지 못했습니다.");
    }

    const data = await res.json();
    setDocuments(data);
  };

  const uploadFile = async () => {
    if (!file) {
      setErrorMessage("업로드할 PDF 파일을 선택해 주세요.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setErrorMessage("");

      const res = await fetch(`${API}/documents/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw await responseError(res, "파일 업로드에 실패했습니다.");
      }

      await fetchDocuments();
      setFile(null);

      const fileInput = document.getElementById("file-input");
      if (fileInput) {
        fileInput.value = "";
      }
    } catch (error) {
      console.error(error);
      setErrorMessage(error.message || "파일 업로드 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const selectDocument = async (id) => {
    try {
      setLoading(true);
      setErrorMessage("");

      const res = await fetch(`${API}/documents/${id}`);
      if (!res.ok) {
        throw new Error("문서 정보를 불러오지 못했습니다.");
      }

      const data = await res.json();
      setSelectedDoc(data);
      setSummary(data.summary || "");
      setQuestion("");
      setAnswer("");
      setSources([]);
      setSearched(false);
    } catch (error) {
      console.error(error);
      setErrorMessage(error.message || "문서 조회 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const summarize = async () => {
    if (!selectedDoc) return;

    try {
      setLoading(true);
      setErrorMessage("");

      const res = await fetch(`${API}/documents/${selectedDoc.id}/summarize`, {
        method: "POST",
      });

      if (!res.ok) {
        throw await responseError(res, "요약 생성에 실패했습니다.");
      }

      const data = await res.json();
      setSummary(data.summary);
      setSelectedDoc((doc) => ({ ...doc, summary: data.summary, status: "summarized" }));
      await fetchDocuments();
    } catch (error) {
      console.error(error);
      setErrorMessage(error.message || "요약 생성 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const queryDocument = async (mode) => {
    if (!selectedDoc) {
      setErrorMessage("먼저 문서를 선택해 주세요.");
      return;
    }

    if (!question.trim()) {
      setErrorMessage("질문을 입력해 주세요.");
      return;
    }

    try {
      setLoading(true);
      setErrorMessage("");
      setAnswer("");
      setSources([]);
      setSearched(false);

      const res = await fetch(`${API}/documents/${selectedDoc.id}/${mode}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) {
        throw await responseError(res, "질문 처리에 실패했습니다.");
      }

      const data = await res.json();
      setAnswer(data.answer || "");
      setSources(data.sources);
      setSearched(true);
    } catch (error) {
      console.error(error);
      setErrorMessage(error.message || "질문 처리 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const renderStatusText = (status) => {
    if (status === "summarized") return "요약 완료";
    if (status === "uploaded") return "업로드 완료";
    if (status === "failed") return "처리 실패";
    return status || "상태 없음";
  };

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>DocInsight AI</h1>
          <p>PDF 업로드, 요약, 문서 기반 질문 응답을 한 곳에서 관리합니다.</p>
        </div>
      </header>

      {errorMessage && <div className="error-banner" role="alert">{errorMessage}</div>}

      <section className="upload-card">
        <div className="upload-left">
          <h2>문서 업로드</h2>
          <p>기본 한도 10 MiB · 200쪽 · 추출 텍스트 100만 자. 텍스트가 있는 PDF를 선택하세요.</p>
        </div>

        <div className="upload-right">
          <input
            id="file-input"
            type="file"
            accept="application/pdf"
            aria-label="업로드할 PDF"
            disabled={loading}
            onChange={(e) => setFile(e.target.files[0])}
          />
          <button className="primary-button" onClick={uploadFile} disabled={loading}>
            업로드
          </button>
        </div>
      </section>

      <main className="layout">
        <aside className="sidebar">
          <div className="panel-header">
            <h3>문서 목록</h3>
            <span>{documents.length}개</span>
          </div>

          <div className="document-list">
            {documents.length === 0 ? (
              <div className="empty-box">업로드된 문서가 없습니다.</div>
            ) : (
              documents.map((doc) => (
                <button
                  key={doc.id}
                  type="button"
                  className={`document-item ${
                    selectedDoc?.id === doc.id ? "active" : ""
                  }`}
                  onClick={() => selectDocument(doc.id)}
                  disabled={loading}
                  aria-pressed={selectedDoc?.id === doc.id}
                >
                  <div className="document-item-top">
                    <strong>{doc.filename}</strong>
                  </div>
                  <div className="document-meta">
                    <span className="status-badge">{renderStatusText(doc.status)}</span>
                    <span>{doc.extracted_text_length} chars</span>
                  </div>
                </button>
              ))
            )}
          </div>
        </aside>

        <section className="content">
          {!selectedDoc ? (
            <div className="empty-state">
              <h2>문서를 선택하세요</h2>
              <p>왼쪽 문서 목록에서 확인할 PDF를 선택하면 상세 정보가 표시됩니다.</p>
            </div>
          ) : (
            <>
              <div className="content-header">
                <div>
                  <h2>{selectedDoc.filename}</h2>
                  <p>
                    상태: <strong>{renderStatusText(selectedDoc.status)}</strong>
                  </p>
                </div>
                <button className="primary-button" onClick={summarize} disabled={loading}>
                  요약 생성
                </button>
              </div>

              <div className="card">
                <h3>문서 요약</h3>
                <p className="help-text">
                  {selectedDoc.extracted_text_length > 12000
                    ? `문서 ${selectedDoc.extracted_text_length.toLocaleString()}자 중 앞 12,000자만 요약합니다.`
                    : "추출된 텍스트를 요약합니다."}
                </p>
                <div className="result-box">
                  {summary ? (
                    <p>{summary}</p>
                  ) : (
                    <p className="placeholder-text">아직 생성된 요약이 없습니다.</p>
                  )}
                </div>
              </div>

              <div className="card">
                <h3>문서 질문</h3>
                <p className="help-text">문서 전체에서 질문의 단어가 포함된 구간을 찾습니다. 문서에 쓰인 구체적인 단어로 질문해 보세요.</p>
                <div className="question-box">
                  <input
                    type="text"
                    value={question}
                    aria-label="문서에 대한 질문"
                    maxLength={1000}
                    disabled={loading}
                    onChange={(e) => {
                      setQuestion(e.target.value);
                      setAnswer("");
                      setSources([]);
                      setSearched(false);
                    }}
                    placeholder="예: 계약 해지 통보 기간은 얼마인가요?"
                  />
                </div>
                <div className="question-actions">
                  <button className="secondary-button" onClick={() => queryDocument("search")} disabled={loading || !question.trim()}>
                    문서에서 찾기
                  </button>
                  <button className="primary-button" onClick={() => queryDocument("ask")} disabled={loading || !question.trim()}>
                    AI로 답변 받기
                  </button>
                </div>
                <p className="help-text">찾기는 API 키 없이 사용할 수 있습니다. AI 답변과 요약은 OpenAI 설정이 필요합니다.</p>

                <div className="result-box" aria-live="polite">
                  {answer ? (
                    <p>{answer}</p>
                  ) : (
                    <p className="placeholder-text">{searched ? "검색 결과를 아래에서 확인하세요." : "질문 결과가 여기에 표시됩니다."}</p>
                  )}
                </div>
                {searched && (
                  <section className="sources" aria-label="검색한 문서 구간">
                    <h4>검색한 문서 구간 · {sources.length}개</h4>
                    <p className="help-text">AI 답변에 제공하는 문맥입니다. 답변의 사실 여부를 자동 검증한 결과는 아닙니다. 위치는 PDF 쪽수가 아닌 추출 텍스트 기준입니다.</p>
                    {sources.length === 0 && <p>일치하는 구간을 찾지 못했습니다. 문서에 쓰인 단어로 다시 검색해 보세요.</p>}
                    {sources.map((source) => (
                      <details key={source.source_id}>
                        <summary>{source.source_id} · 문자 위치 {source.start_char}–{source.end_char}</summary>
                        <p>{source.text}</p>
                      </details>
                    ))}
                  </section>
                )}
              </div>
            </>
          )}
        </section>
      </main>

      {loading && <div className="loading-overlay">처리 중...</div>}
    </div>
  );
}
