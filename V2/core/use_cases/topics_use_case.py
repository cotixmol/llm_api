from datetime import datetime
from V2.api.dtos.topics_dto import TopicsRequest, TopicsResponse
from V2.core.interfaces.repositories.topics_repository_interface import TopicsRepositoryInterface


class TopicsUseCase:
    """
    Caso de uso para manejar requests de tópicos:
    - Valida parámetros de fecha
    - Obtiene documentos
    - Ejecuta pipeline de tópicos
    """

    def __init__(self, topics_repository: TopicsRepositoryInterface):
        self.topics_repository = topics_repository

    async def execute(self, request: TopicsRequest) -> TopicsResponse:

        # 1) Obtener documentos
        documents = await self.topics_repository.fetch_documents_for_topics(request)

        # 2) Si no hay documentos, devolver respuesta vacía
        if not documents:
            return TopicsResponse(data=[], chart={}, n_docs=0)

        # 3) Ejecutar pipeline (modelado, enriquecimiento y mapeo)
        return await self.topics_repository.process_topics_pipeline(documents)
