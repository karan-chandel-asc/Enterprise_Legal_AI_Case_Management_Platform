from Enterprise_Legal_AI_Case_Management_Platform.logger import logger
from case_management.models import Case, CaseDocuments
from chatbot.services.embedding import EmbeddingService
from chatbot.services.query_analysis import GREETING_REPLY, analyze_search_query
from chatbot.services.vector_storage import PineconeService

TOP_K = 15


class SemanticSearchService:
    def search(self, user, query, case_id=None, top_k=TOP_K):
        """Run semantic search after Groq query analysis.

        Returns data shaped as:
          {
            "query_type": "greeting" | "case_related",
            "keywords": [...],
            "reply": str | None,   # set for greetings
            "results": [...],
          }
        """
        try:
            query = (query or "").strip()
            if not query:
                return False, "Query cannot be empty", None

            analysis = analyze_search_query(query)
            query_type = analysis["query_type"]
            keywords = analysis["keywords"]

            if query_type == "greeting":
                payload = {
                    "query_type": "greeting",
                    "keywords": [],
                    "reply": GREETING_REPLY,
                    "results": [],
                }
                try:
                    from analytics.services import AnalyticsService
                    AnalyticsService.track(
                        "search.queried",
                        user=user,
                        status="info",
                        page="search",
                        message="greeting_blocked",
                        metadata={"case_id": case_id, "query_len": len(query)},
                    )
                except Exception:
                    pass
                return True, "Please ask a case-related query", payload

            cases_qs = Case.objects.filter(user=user)
            if case_id is not None:
                cases_qs = cases_qs.filter(id=case_id)
                if not cases_qs.exists():
                    return False, "Case not found", None

            documents = CaseDocuments.objects.filter(case__in=cases_qs).select_related("case")
            doc_meta = {}
            for d in documents:
                file_url = d.document_file.url if d.document_file else None
                name = d.document_name or ""
                ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                if ext == "pdf":
                    file_type = "pdf"
                elif ext in ("doc", "docx"):
                    file_type = "docx"
                else:
                    file_type = ext or "file"
                doc_meta[str(d.id)] = {
                    "case_id": d.case_id,
                    "case_title": d.case.case_title,
                    "case_number": d.case.case_id,
                    "doc_id": d.id,
                    "file_url": file_url,
                    "file_type": file_type,
                }
            doc_ids = list(doc_meta.keys())

            if not doc_ids:
                return True, "No indexed documents to search yet", {
                    "query_type": "case_related",
                    "keywords": keywords,
                    "reply": None,
                    "results": [],
                }

            embedding_service = EmbeddingService()
            query_vec = embedding_service.embed_query(query)
            matches = PineconeService(embedding_service).query(doc_ids, query_vec, top_k=top_k)

            results = []
            for m in matches:
                meta = doc_meta.get(m.get("doc_id", ""))
                if not meta:
                    continue
                results.append({
                    "doc_id": meta["doc_id"],
                    "doc_name": m["doc_name"],
                    "page": m["page"],
                    "text": m["text"],
                    # Pinecone cosine similarity (0–1). Higher = closer meaning match.
                    "score": round(float(m["score"] or 0), 4),
                    "case_id": meta["case_id"],
                    "case_title": meta["case_title"],
                    "case_number": meta["case_number"],
                    "file_url": meta["file_url"],
                    "file_type": meta["file_type"],
                })

            try:
                from analytics.services import AnalyticsService
                AnalyticsService.track(
                    "search.queried",
                    user=user,
                    status="succeeded",
                    page="search",
                    metadata={
                        "case_id": case_id,
                        "result_count": len(results),
                        "query_len": len(query),
                        "keywords": keywords[:8],
                    },
                )
            except Exception:
                pass

            return True, "Search completed successfully", {
                "query_type": "case_related",
                "keywords": keywords,
                "reply": None,
                "results": results,
            }
        except Exception as e:
            logger.error(f"Error in SemanticSearchService.search: {e}")
            try:
                from analytics.services import AnalyticsService
                AnalyticsService.track(
                    "search.queried",
                    user=user,
                    status="failed",
                    page="search",
                    message=str(e)[:255],
                    metadata={"case_id": case_id},
                )
            except Exception:
                pass
            return False, f"Error running search: {e}", None
