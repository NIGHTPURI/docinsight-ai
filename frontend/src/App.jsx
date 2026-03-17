import { useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [documentId, setDocumentId] = useState(null);
  const [filename, setFilename] = useState("");
  const [summary, setSummary] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    setFile(selectedFile || null);
    setError("");
    setSummary("");
    setAnswer("");
    setDocumentId(null);
    setFilename(selectedFile?.name || "");
  };

  const handleUploadAndSummarize = async () => {
    if (!file) {
      setError("PDF 파일을 선택해 주세요.");
      return;
    }

    setLoading(true);
    setError("");
    setSummary("");
    setAnswer("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const uploadResponse = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: "POST",
        body: formData,
      });

      const uploadData = await uploadResponse.json();

      if (!uploadResponse.ok) {
        throw new Error(uploadData.detail || "파일 업로드에 실패했습니다.");
      }

      const newDocumentId = uploadData.document_id;
      setDocumentId(newDocumentId);

      const summarizeResponse = await fetch(
        `${API_BASE_URL}/documents/${newDocumentId}/summarize`,
        {
          method: "POST",
        }
      );

      const summarizeData = await summarizeResponse.json();

      if (!summarizeResponse.ok) {
        throw new Error(summarizeData.detail || "문서 요약에 실패했습니다.");
      }

      setSummary(summarizeData.summary);
    } catch (err) {
      setError(err.message || "알 수 없는 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const handleAsk = async () => {
    if (!documentId) {
      setError("먼저 문서를 업로드하고 요약해야 합니다.");
      return;
    }

    if (!question.trim()) {
      setError("질문을 입력해 주세요.");
      return;
    }

    setAsking(true);
    setError("");
    setAnswer("");

    try {
      const response = await fetch(`${API_BASE_URL}/documents/${documentId}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "질문 처리에 실패했습니다.");
      }

      setAnswer(data.answer);
    } catch (err) {
      setError(err.message || "질문 처리 중 오류가 발생했습니다.");
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="page">
      <div className="container">
        <header className="hero">
          <p className="badge">AI Document Summarizer</p>
          <h1>DocInsight AI</h1>
          <p className="subtitle">
            PDF 문서를 업로드하면 텍스트를 추출하고 AI가 핵심 내용을 요약합니다.
          </p>
        </header>

        <section className="card">
          <h2>1. PDF 업로드</h2>
          <div className="upload-box">
            <input type="file" accept=".pdf" onChange={handleFileChange} />
            {filename && <p className="filename">선택된 파일: {filename}</p>}
            <button onClick={handleUploadAndSummarize} disabled={loading}>
              {loading ? "업로드 및 요약 중..." : "업로드하고 요약하기"}
            </button>
          </div>
        </section>

        {error && (
          <section className="card error-card">
            <p>{error}</p>
          </section>
        )}

        <section className="card">
          <h2>2. 요약 결과</h2>
          <div className="result-box">
            {summary ? (
              <p>{summary}</p>
            ) : (
              <p className="placeholder">아직 요약 결과가 없습니다.</p>
            )}
          </div>
        </section>

        <section className="card">
          <h2>3. 문서에 질문하기</h2>
          <div className="qa-box">
            <textarea
              placeholder="예: 이 문서의 핵심 목적은 무엇인가요?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={4}
            />
            <button onClick={handleAsk} disabled={asking || !documentId}>
              {asking ? "질문 처리 중..." : "질문하기"}
            </button>
          </div>
          <div className="result-box">
            {answer ? (
              <p>{answer}</p>
            ) : (
              <p className="placeholder">
                문서를 업로드한 뒤 질문을 입력하면 답변이 표시됩니다.
              </p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;