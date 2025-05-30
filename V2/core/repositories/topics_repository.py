from typing import List
from V2.api.dtos.common_dto import BaseDocument
from V2.api.dtos.topics_dto import TopicsRequest, TopicsResponse
from V2.core.interfaces.repositories.topics_repository_interface import TopicsRepositoryInterface
from V2.core.interfaces.services.document_search_service_repository_interface import (
    DocumentSearchServiceRepositoryInterface,
)
from V2.core.interfaces.services.llm_service_repository_interface import (
    LLMServiceRepositoryInterface,
)
from V2.core.interfaces.services.topics_modelling_service_repository_interface import (
    TopicsModellingServiceRepositoryInterface,
)
from V2.core.mappers.topics_response_mapper import map_to_response

class TopicsRepository(TopicsRepositoryInterface):
    def __init__(
        self,
        document_search_service_repository: DocumentSearchServiceRepositoryInterface,
        topics_modelling_repository: TopicsModellingServiceRepositoryInterface,
        llm_service_repository: LLMServiceRepositoryInterface,
    ):
        self.search_repo = document_search_service_repository
        self.topic_model_repo = topics_modelling_repository
        self.llm_repo = llm_service_repository

    async def fetch_documents_for_topics(
        self, request: TopicsRequest
    ) -> List[BaseDocument]:
        return await self.search_repo.get_documents(request)

    async def process_topics_pipeline(
        self, documents: List[BaseDocument]
    ) -> TopicsResponse:
        # 1. Modelado puro: UMAP/HDBSCAN + BERTopic
        raw = await self.topic_model_repo.get_raw_analysis(documents)

        # 2. Preparar input para LLM: keywords y documentos representativos
        summary_inputs = []
        for tid in range(raw.num_topics):
            keywords = [w for w, _ in raw.topics_dict.get(tid, [])]
            docs_for_tid = (
                raw.doc_info[raw.doc_info["Topic"] == tid]["Document"].tolist()
            )
            summary_inputs.append({"topic_id": tid, "keywords": keywords, "docs": docs_for_tid})

        # 3. Enriquecimiento con LLM
        enriched = await self.llm_repo.enrich_topics(summary_inputs)

        # 4. Mapeo a DTO y creación de charts
        response = map_to_response(raw, enriched)
        return response
