# 문서 후반부 검색과 실패 경계 검증

## 해결한 문제

기존 Q&A는 문서의 첫 12,000자만 모델에 전달했다. 계약 해지 조건처럼 뒤에 있는 내용을 묻더라도 모델은 해당 구간을 볼 수 없었다. 전체 텍스트를 그대로 전송하는 대신 로컬 어휘 검색 후 최대 4개 구간을 전달하도록 바꿨다. `/search`와 UI에서 동일한 원문·위치를 확인할 수 있다.

기존 서버는 시작할 때 OpenAI client를 생성하여 키 없이 업로드도 시연하기 어려웠다. client 생성을 AI 요청 시점으로 옮겨 업로드·검색의 외부 API 의존성을 제거했다.

## 변경과 설계 판단

- `app/services/retrieval_service.py`: 순수 함수 검색. 청크 크기 1,200, 간격 1,000, 최대 4개, 중복 범위 제거. 검색용 정규화와 원문 표시를 분리한다. 외부 검색 서비스나 새로운 모델 비용 없이 테스트 가능하다.
- `app/upload_limit.py`, `pdf_service.py`: multipart 이전 본문 제한과 이후 실제 파일·PDF 페이지·추출 문자 검증을 별도로 둔다. 거짓 Content-Length나 chunked 전송도 실제 수신량으로 거부한다. 매우 큰 Content-Length는 정수 변환 대신 십진수 바이트 비교로 처리한다.
- `ai_service.py`: 지연 생성·종료되는 SDK client, 재시도 없음, 출력·timeout 설정, 잘리거나 빈 응답 거부, 외부 오류 내용 미노출. Chat Completions와 기존 기본 모델 설정은 유지한다.
- `routers/documents.py`, `schemas.py`: 검색 endpoint, 답변 근거 metadata, 일치 없을 때 모델 미호출, 요약 범위 metadata. 동기 PDF 추출은 thread pool에서 실행한다.
- `database.py`, repository: 테스트용 SQLite shared in-memory 연결과 commit 이후 객체 접근을 명시한다. 업로드 DB 오류 시 rollback과 파일 정리를 검증한다. 기존 데이터 모델 변경·migration은 없다.
- React: 검색/AI 버튼 분리, 검색 원문 펼치기, 요약 범위, 오류 alert, 요청 중 입력 비활성화, 질문·문서 변경 시 이전 근거 제거. React가 원문을 텍스트로 렌더링하며 HTML로 삽입하지 않는다.
- 의존성: Python pinned version은 그대로 유지하고 UTF-16 requirements를 UTF-8로 변환. npm은 기존 semver 범위 내 패치. 생성 DB의 Git 추적을 중단하며 해당 로컬 파일과 과거 history는 보존한다.

## 자동 검증

2026-11-01 Python 3.12, Node 22:

```bash
python -m unittest discover -s tests -v
cd frontend
npm run lint
npm run build
```

34개 테스트 통과. 주요 사례:

| 영역 | 확인한 동작 |
|---|---|
| 실제 합성 PDF API | 25쪽의 앞부분을 넘어 마지막 페이지의 `Cancellation notice requires 45 days` 검색. 해당 문장이 추출 문자 위치 12,000 이후임을 먼저 확인 |
| AI 입력 | 후반부 원문이 포함되고 문맥은 5,000자 미만. 반환 source와 검색 결과 일치 |
| 검색 | 한국어 조사 일부, case normalization, Unicode 원문 위치, 결정적 순위, 최대 4개 겹치지 않는 구간, 무관 질문 abstention |
| 업로드 | 경로가 들어간 파일명, 잘못된 PDF, 텍스트 없는 PDF, 파일/페이지/문자 초과, DB 실패 정리 |
| 파싱 전 제한 | chunked, 거짓 크기 헤더, 정확한 경계, 과도한 헤더, 5,000자리 Content-Length |
| 외부 실패 | 누락 키·빈 응답·truncated 응답·timeout·connection 오류, 재시도 0·client 종료, 실패한 답변 미저장 |
| 요청·UI 빌드 | 빈 질문/길이 한도/없는 문서, summary cache와 범위, CORS, ESLint 및 Vite build |

테스트는 API client mock과 실제 OpenAI SDK + httpx MockTransport를 함께 사용해 호출 계약·직렬화·응답 파싱을 검증한다. 네트워크 transport는 사용하지 않는다. 실제 모델의 사실성, 인용 정확도, 비용 또는 지연 개선을 측정하지 않았다. `tests/test_documents.py`는 런타임에 PDF를 생성하므로 실제 사용자 문서가 fixture에 들어가지 않는다.

추가 경계 테스트는 파일이 정확히 한도 크기일 때 성공하고 1바이트 초과 시 거부되는지, 파싱 전 413에도 CORS 헤더가 포함되는지, 추출이 취소될 때 rollback과 파일 정리가 되는지 확인한다.

## 실제 브라우저 확인

Playwright CLI + Chromium, 별도 SQLite DB, API 키 없는 서버에서 합성 26쪽 PDF를 업로드했다. 추출 텍스트 35,877자 중 `[35000, 35877)`의 해지 통보 45일 조건이 검색되고 원문을 펼쳐 볼 수 있음을 DOM assertion으로 확인했다. 데스크톱 1440px와 모바일 390px에서 가로 넘침이 없고, 질문을 수정하면 이전 구간이 사라지며 일치 없는 질문에는 안내가 표시된다. 키 없는 AI 요청의 503 안내도 확인했다. 해당 요청의 브라우저 HTTP 오류는 의도한 결과다.

한글 글꼴이 없는 WSL에는 이미 설치된 Windows Malgun Gothic을 사용자 fontconfig에 연결해 한글 표시를 확인했다. 글꼴 파일은 저장소에 포함하지 않는다. 화면 증거는 [데스크톱](evidence/desktop-evidence.png)과 [모바일](evidence/mobile-evidence.png)에 있다. 브라우저 확인은 로컬 검증이며 CI에서는 백엔드 테스트와 프런트엔드 린트·빌드를 실행한다.

## Opus 검토 반영

Kiro CLI에서 실제 `claude-opus-5.5`와 3회 토론한 결과를 반영했다. 업로드 취소 정리 및 실제 SDK의 MockTransport 테스트를 추가하고, 응답 상태를 `generated`로 명명해 답변 정확성을 뜻하지 않게 했다. 질문 길이, multipart 여유 64 KiB, CORS 외부 배치는 이미 구현되어 있었으며 테스트로 확인했다. 요약은 앞부분만 처리하고 질문 이력은 검색 구간을 영속화하지 않는 한계를 명시했다.

ASGI 요청 본문은 한도까지 메모리에 버퍼링한다. 조기 413을 일부 클라이언트가 연결 종료로 표시할 수 있고, 프로세스 강제 종료·파서 강제 중단을 복구하는 작업 시스템은 아니다. 이 제한은 PDF 파서의 최대 메모리나 전체 처리 시간 보장이 아니다.

## 의존성 감사

`npm audit fix --ignore-scripts`로 호환 가능한 업데이트를 적용했다. 최초 19개(높음 10, 중간 8, 낮음 1)에서 중간 6개로 감소했다. 남은 항목은 `minimatch` globparts 증폭 advisory와 연결된 ESLint 개발 도구 체인이다. 감사 도구는 이 체인에 `No fix available`을 보고했으며 무검증 major override는 넣지 않았다. 이는 전체 시스템 보안 인증을 의미하지 않는다.

## 한계

검색은 모든 청크를 훑고 점수를 정렬하므로 추출 문자 수를 L, 청크 수를 C, 질문의 고유 단어 수를 Q라 할 때 대략 O(L + CQ + C log C) 시간, O(L + Q) 공간을 사용한다. 질문 길이는 1,000자로 제한한다. 새 업로드는 최대 100만 문자이며 기존 DB에는 제한이 소급되지 않는다. PDF 파싱 자체, 동시성, 호스팅 수준의 제한은 별도 문제다.

검색 원문은 검토 가능한 입력 근거일 뿐 출력 주장에 대한 검증서가 아니다. 구간 경계가 문장을 자를 수 있고 단어가 달라도 같은 의미인 질문은 놓칠 수 있다. 도메인 문서로 별도 retrieval/answer 평가를 한 뒤 임베딩이나 reranker 필요성을 판단하는 것이 다음 단계다.
