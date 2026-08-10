from django.core.paginator import EmptyPage, Paginator
from django.db.models import Q

from case_management.pipeline.base_pipeline import BasePipeline
from case_management.services.db_mechanism import DbMechanism
from Enterprise_Legal_AI_Case_Management_Platform.logger import logger


class CaseListPipeline(BasePipeline):
    def __init__(self, request, filters):
        self.request = request
        self.filters = filters
        self.db_mechanism = DbMechanism()

    def process_item(self):
        try:
            cases = self.db_mechanism.get_cases(self.request)

            counts = {
                "total": cases.count(),
                "active": cases.filter(case_status="active").count(),
                "closed": cases.filter(case_status="closed").count(),
            }

            search = self.filters.get("search")
            if search:
                cases = cases.filter(
                    Q(case_title__icontains=search)
                    | Q(case_id__icontains=search)
                    | Q(client_name__icontains=search)
                )

            if self.filters.get("case_type"):
                cases = cases.filter(case_type=self.filters["case_type"])

            if self.filters.get("case_status"):
                cases = cases.filter(case_status=self.filters["case_status"])

            cases = cases.order_by("-case_created_at")

            page_size = self.filters.get("page_size", 10)
            paginator = Paginator(cases, page_size)

            try:
                page_obj = paginator.page(self.filters.get("page", 1))
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)

            payload = {
                "cases": list(page_obj.object_list),
                "pagination": {
                    "page": page_obj.number,
                    "page_size": page_size,
                    "total_pages": paginator.num_pages,
                    "total_results": paginator.count,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous(),
                },
                "counts": counts,
            }
            return True, "Cases fetched successfully", payload
        except Exception as e:
            logger.error(f"Error in CaseListPipeline: {e}")
            return False, f"Error getting cases: {e}", None
