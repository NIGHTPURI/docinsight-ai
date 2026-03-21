import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

export default function App() {
  const [file, setFile] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [summary, setSummary] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
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
        const errorData = await res.json().catch(() => null);
        throw new Error(errorData?.detail || "파일 업로드에 실패했습니다.");
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
        const errorData = await res.json().catch(() => null);
        throw new Error(errorData?.detail || "요약 생성에 실패했습니다.");
      }

      const data = await res.json();
      setSummary(data.summary);

      await fetchDocuments();
      await selectDocument(selectedDoc.id);
    } catch (error) {
      console.error(error);
      setErrorMessage(error.message || "요약 생성 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const ask = async () => {
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

      const res = await fetch(`${API}/documents/${selectedDoc.id}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => null);
        throw new Error(errorData?.detail || "질문 처리에 실패했습니다.");
      }

      const data = await res.json();
      setAnswer(data.answer);
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

      {errorMessage && <div className="error-banner">{errorMessage}</div>}

      <section className="upload-card">
        <div className="upload-left">
          <h2>문서 업로드</h2>
          <p>PDF 파일을 업로드하면 문서 목록에 추가됩니다.</p>
        </div>

        <div className="upload-right">
          <input
            id="file-input"
            type="file"
            accept="application/pdf"
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
                <div className="question-box">
                  <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="예: 이 문서의 핵심 내용은 무엇인가요?"
                  />
                  <button className="primary-button" onClick={ask} disabled={loading}>
                    질문하기
                  </button>
                </div>

                <div className="result-box">
                  {answer ? (
                    <p>{answer}</p>
                  ) : (
                    <p className="placeholder-text">질문 결과가 여기에 표시됩니다.</p>
                  )}
                </div>
              </div>
            </>
          )}
        </section>
      </main>

      {loading && <div className="loading-overlay">처리 중...</div>}
    </div>
  );
}