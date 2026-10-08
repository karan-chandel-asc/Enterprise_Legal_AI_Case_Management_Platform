# Lexora — Case Study Facts (verified from the code)

Every fact has a source file. "NOT FOUND" means the project does not contain it.
I did not run any evaluation, because none exists (see section 5).

Changes made on 2026-10-08 (not yet tested end to end, so re-test before any demo):
- `chatbot/tasks.py`: page numbers are now stored 1-based.
- `chatbot/services/rag_graph.py`: the answer now lists only the sources it cites, and each citation stores its passage text.
- `chatbot/services/chat_service.py`: each citation stores its file link.
- `static/js/case-detail.js`: clicking a source chip opens a modal with the passage.

---

## 1. PROJECT SUMMARY

**What it does (plain words).** Lexora is a web app for law firms. A lawyer creates a case and uploads its documents (PDF, Word, text, CSV). The app reads them in the background. The lawyer can then ask questions about a case, or search across cases. Answers come from the uploaded documents and show the document name and page number they came from.
Source: `README.md`, `case_management/services/document_service.py`, `chatbot/services/rag_graph.py`

**Who it is for.** Law firms and legal teams (README: "full-stack legal workspace for law firms and legal teams"). Source: `README.md`.

The README itself says it is a "Portfolio / Upwork project". Source: `README.md`.

---

## 2. TECH STACK (only what is used)

| Item | What the code uses | Source |
|---|---|---|
| Language | Python (README says 3.11+, Dockerfile uses 3.12) | `README.md`, `Dockerfile` |
| Web framework | Django 5.2 + Django REST Framework | `README.md`, `requirements.txt` |
| Chat/search API | FastAPI + Uvicorn (separate service, port 8001 locally) | `chatbot/fastapi_app/main.py` |
| RAG orchestration | LangGraph (retrieve → generate / no_context) | `chatbot/services/rag_graph.py` |
| Answer LLM | Groq, model `openai/gpt-oss-120b`, temperature 0.2 | `chatbot/services/rag_graph.py` |
| Query-analysis LLM | Groq, model `llama-3.1-8b-instant` (greeting check and keywords for search) | `chatbot/services/query_analysis.py` |
| Embeddings | Cohere `embed-english-v3.0` (documents and queries use different input types) | `chatbot/services/embedding.py` |
| Vector database | Pinecone, cosine metric, dimension 1024 (index is created in code if missing) | `chatbot/services/vector_storage.py` |
| Background jobs | Celery + Redis | `Enterprise_Legal_AI_Case_Management_Platform/settings.py` |
| Database | SQLite locally, Postgres 16 when `POSTGRES_HOST` is set (Docker) | `settings.py`, `docker-compose.yml` |
| Frontend | Django templates, custom CSS, plain JavaScript (landing page uses Tailwind and Alpine.js from a CDN) | `README.md`, `static/`, `templates/` |
| File storage | Local `media/` folder (not S3) | `settings.py` (`MEDIA_ROOT`) |
| Deployment | Docker Compose: nginx, Gunicorn (2 workers), FastAPI, Celery worker, Celery beat, Redis, Postgres | `docker-compose.yml`, `Dockerfile`, `nginx/default.conf` |
| AWS | **EC2 only** (one instance, per the guide). No S3, RDS, or other AWS service is used. | `DEPLOY_AWS.md` |

Not used: reranker, hybrid/keyword search, OCR. Gemini and OAuth keys are unused. Source: `README.md` ("Unused today").

---

## 3. HOW THE RAG PIPELINE WORKS

**Upload and file types**
- Allowed extensions: `.pdf`, `.docx`, `.doc`, `.txt`, `.csv`. Maximum size is 25 MB. Source: `case_management/services/document_service.py`.
- The upload returns immediately. A Celery task, `process_document_embedding`, does the indexing. Source: same file, `chatbot/tasks.py`.
- The loader handles only `.pdf`, `.csv`, `.txt`, `.docx`. **`.doc` is accepted at upload but then fails to load** ("Unsupported file type"). Source: `chatbot/services/loaders.py`.
- PDF text comes from `PyPDFLoader`, so only text-based PDFs work. No OCR code exists. A scanned PDF ends as status "failed: No extractable text". Source: `chatbot/services/loaders.py`, `chatbot/tasks.py`.

**Chunking**
- Each page is split separately with `RecursiveCharacterTextSplitter`: chunk size 500 characters, overlap 100 characters. Source: `chatbot/services/chunking.py`, `chatbot/tasks.py`.
- Chunks never cross a page boundary, so every chunk belongs to exactly one page.
- Each chunk is stored in Pinecone with its text, document id, document name and page number, in batches of 100. Source: `chatbot/services/vector_storage.py`.

**Retrieval**
- Chat: top-k = 6, restricted to the documents of that one case. Source: `rag_graph.py` (`TOP_K = 6`).
- Search: top-k = 15, restricted to the documents of the logged-in user's cases (or one chosen case). Source: `chatbot/services/search_service.py` (`TOP_K = 15`).
- Pinecone filter: `doc_id $in [the allowed document ids]`. Source: `vector_storage.py`.
- Reranking: NOT FOUND. Minimum-score cutoff: NOT FOUND.
- Chat history: the last 10 messages are added to the prompt. Source: `chat_service.py` (`HISTORY_TURNS = 10`).

**Where the page number comes from**
1. The PDF loader reads each page separately, and each page carries its page index in its metadata.
2. `chatbot/tasks.py` stores that number, plus 1, as `page` on every chunk of that page. Before 2026-10-08 it stored the raw 0-based index, which was off by one.
3. Retrieval returns the chunk with its stored `page` and `doc_name`.
4. The prompt labels each excerpt `[n] (document name, p.page)`, and the model is told to cite by bracket number. Source: `rag_graph.py`.
5. After generation, the code keeps only the sources whose `[n]` appears in the answer. It removes bracket numbers that don't match a real excerpt. If the model cites nothing, all retrieved sources are shown.
6. The page number is therefore read from the stored chunk, not written by the LLM. The LLM only chooses which numbered excerpt to cite.

**Page caveats**
- Documents indexed before the fix still hold 0-based pages. All 16 documents in the local database were indexed before the fix (`db.sqlite3`), so they need re-indexing.
- For non-PDF files "page" is not a real page. `.docx` and `.txt` load as one document, so every chunk shows page 1. CSV loads one document per row, so "page" is the row number. Source: `chatbot/services/loaders.py`, `chatbot/tasks.py`.

**Guardrails against wrong answers**
- System prompt: answer "strictly using the numbered context excerpts", don't invent facts, and say so if the excerpts don't contain enough information. Source: `rag_graph.py` (`SYSTEM_PROMPT`).
- If retrieval returns nothing, the graph skips the LLM and returns a fixed message: "I couldn't find anything relevant…". Source: `rag_graph.py` (`no_context_node`).
- If the case has no documents, chat returns a fixed "no documents indexed yet" message. Source: `chat_service.py`.
- Greeting or chitchat in the search box is blocked with a "Please ask a case-related query" reply. Source: `query_analysis.py`, `search_service.py`.
- Limits: Pinecone always returns its nearest chunks if any exist, because there is no score cutoff. The "answer only from the excerpts" rule is a prompt instruction, not a code-enforced check. The code checks that `[n]` markers are valid. It does not check that the sentence is actually supported by that excerpt.

---

## 4. FEATURES THAT EXIST

- Register, login, logout, forgot/reset password with an emailed one-time code. Source: `auth_app/`.
- Optional MFA code per user (a Profile toggle). Source: `auth_app/pipelines/login_pipeline.py`, `auth_app/feature_flags.py`.
- Case create, list, update, delete. Source: `case_management/`.
- Document upload, background indexing with status (pending, processing, completed, failed) and chunk count, and delete with vector cleanup. Source: `case_management/models.py`, `chatbot/tasks.py`.
- Per-case AI Assistant chat with saved history. Source: `chatbot/models.py`, `chat_service.py`.
- Source chips on answers: document name, page, and (since 2026-10-08) a modal showing the exact passage plus an "Open page in document" button for PDFs. Source: `static/js/case-detail.js`.
- Semantic search across all cases or one case, with similarity %, highlighted snippet, and "open PDF at page". Source: `static/js/search.js`, `search_service.py`.
- Hearings calendar and CRUD, case notes, activity feed, dashboard KPIs. Source: `README.md`, `case_management/`, `dashboard/`.
- Analytics events and an optional daily email digest. Source: `analytics/`, `settings.py`.

---

## 5. MEASURABLE FACTS

| Fact | Value | Source |
|---|---|---|
| Automated tests | **0.** All four `tests.py` files contain only the Django template comment. | `*/tests.py` |
| Evaluation script / accuracy test set | NOT FOUND | whole repo |
| Logged response times | NOT FOUND. `app.log` has no latency or timing lines. | `app.log` |
| Upload limit | 25 MB in the app (nginx allows 50 MB) | `document_service.py`, `nginx/default.conf` |
| Timeouts | 120 s for Gunicorn and for nginx proxy reads | `Dockerfile`, `nginx/default.conf` |
| Sample documents in `media/` | 5 distinct PDFs: FIR report, seizure memo, witness statement, CCTV report, crime-scene inspection. 16 stored files, because several are duplicate uploads. | `media/case_documents/` |
| Local database (`db.sqlite3`) | 16 documents, all status "completed"; 86 chunks in total (3 to 7 per document); file sizes 3 KB to 70 KB; 6 cases; 15 user accounts; 10 chat answers, all 10 with citations | `db.sqlite3` (read-only query) |
| Git commits | 5 | `git log` |
| Portfolio assets | 8 screenshots and a demo video, about 0.2 MB | `screenshots/`, `demo/` |

Note: the sample documents are small (3 to 7 chunks each). That shows the pipeline works. It says nothing about large documents.

**How you can measure accuracy and speed yourself**
- Make a test set of 20 to 30 questions, each with a known answer page. Run them against the chat API. Count how often the cited page contains the answer ("citation hit rate"), and note the wrong or "can't find" answers.
- Time the chat and search API calls (for example 20 runs each) and report the median and the slowest.
- Time upload to "completed" for a 10-page and a 100-page PDF.

Report only the numbers you actually get.

---

## 6. SECURITY & PRIVACY FACTS

- **Login:** email and password, using Django's built-in password hashing and Django sessions (cookie `sessionid`). Source: `auth_app/models.py`, `auth_app/services/authentication.py`.
- **Chat/search service:** it reads the same Django session cookie and checks a CSRF header and cookie match. There are no separate tokens. Source: `chatbot/fastapi_app/auth.py`.
- **Data separation:** search and chat only look at cases owned by the logged-in user (`Case.objects.filter(user=...)`). Pinecone queries are filtered to those cases' document ids. Source: `search_service.py`, `chat_service.py`.
- **MFA:** exists, but is off by default and only works per user if they turn it on. Email verification is off by default. Source: `auth_app/feature_flags.py`, `README.md`.
- **Files:** stored unencrypted on the server disk in `media/`. Document text is also stored in Pinecone as metadata. Chunk text is sent to Cohere (embeddings) and Groq (answers). Source: `settings.py`, `vector_storage.py`, `embedding.py`, `rag_graph.py`.
- **Encryption at rest:** NOT FOUND in the code. HTTPS: the deploy guide uses plain HTTP and lists HTTPS as "optional later". Source: `DEPLOY_AWS.md`.
- **Compliance claims (SOC 2, GDPR, HIPAA, etc.):** NOT FOUND. Do not claim them.

---

## 7. GAPS & RISKS (do NOT claim these / things that can break a demo)

**Do not claim**
- "Secure", "bank-level", "encrypted", or compliant. The landing page says "secure and reliable" and "thousands of pages in seconds" (`templates/landing.html`), and neither is backed by any test or measurement.
- "No hallucinations" or "100% accurate". The code reduces the risk (prompt rule, valid citation markers, fixed no-context reply) but cannot guarantee it. There are no accuracy numbers.
- OCR / scanned-document support, `.doc` support, or a reranker. None work or exist.
- Real page numbers for Word, text, or CSV files (see section 3).
- Production AWS deployment. The repo has a deploy guide, but I found no proof of a live deployment.

**Things that could break a demo**
1. **Old indexed documents have page numbers one too low.** Re-index them before any demo (the 16 local documents all need this).
2. **Embedding batch size is unbounded.** `get_embeddings` sends all of a document's chunks to Cohere in one call (`embedding.py`), but Cohere documents a limit of 96 texts per request (this limit comes from Cohere's docs, not the repo). A large PDF with more than 96 chunks may fail. The local samples have at most 7 chunks, so this was never exercised.
3. **Celery worker must be running and Redis reachable**, or uploads stay "pending" with nothing to search or chat with. Source: `README.md` troubleshooting.
4. **On Windows, deep OneDrive paths break LangChain imports.** In this session the project's own `.venv` hit exactly this. Source: README "Windows long-path note".
5. **No automated tests**, so changes can break things unnoticed. The changes made on 2026-10-08 have not been run end to end.
6. **No minimum-score cutoff.** An off-topic question can still retrieve weak chunks, and the model then decides whether to say "not enough information".
7. **Security problems to fix before giving a client a demo link:**
   - `settings.py` has a hard-coded fallback secret key, and debug mode defaults to on, if the environment variables are not set.
   - `nginx/default.conf` serves `/media/` without a login check, so anyone who has a document's URL can open it.
   - `app.log` contains one-time login codes and email addresses in plain text (`auth_app` OTP logging). Don't share the log, and remove that logging.
8. **Citation chips on older chat messages** show "Excerpt unavailable", because they were saved without the passage text.

---

## 8. SUGGESTED CASE STUDY WORDING

Wording only uses facts above. Add measured numbers (section 5) before publishing.

**Case study (about 120 words)**

> **Lexora: an AI assistant for legal case files.** Law firms keep evidence, statements and filings in many PDFs. I built a system where a lawyer uploads documents to a case and asks questions in plain English. Each file is read in the background, split into 500-character passages, and stored in a vector database (Pinecone) using Cohere embeddings. Answers are written by an LLM (via Groq) using only the retrieved passages, and every answer lists its sources as clickable document-and-page references that open the exact passage. If nothing relevant is found, it says so instead of guessing. Each user can only search their own cases. Built with Django, FastAPI, LangGraph and Celery, and packaged with Docker. It currently works with text-based PDFs; page-level citations apply to PDFs.

**One-line portfolio description**

> Lexora: a document Q&A and semantic search app for legal cases, built with Django, FastAPI, LangGraph, Pinecone and Cohere, where each answer cites its source document and page.
