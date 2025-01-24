from typing import List, Tuple, Dict
from api.config.logger import logger
from api.dtos.responses_dtos import LLMClassificationResponse
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from core.repositories.query_repository import Query
from core.repositories.llm_repository import LLMRepository
import iso8601

import re

_N_DOCS = 0

class GetPromptResponseCase:
    def __init__(
            self,
            es_repository: ElasticsearchRepository,
            query_repository: Query,
            llm_repository: LLMRepository,
            index_pattern: str,
            since_date: str,
            to_date: str,
            extra_args: dict,
            prompt: str, 
            task_key: str,
            update_field:str
    ):
        since_iso_time = iso8601.parse_date(since_date).isoformat()
        to_iso_time = iso8601.parse_date(to_date).isoformat()
        self.query_repository = query_repository      
        self.es_repository = es_repository
        self.llm_repository = llm_repository
        self.index_pattern = index_pattern
        self.since_iso_time = since_iso_time
        self.to_iso_time = to_iso_time
        self.extra_args = extra_args
        self.prompt = prompt
        self.task_key = task_key
        self.update_field = update_field

    async def __call__(self) -> LLMClassificationResponse:
        ### CREATE QUERY ###
        self.query_repository.set_date_range(
            since_iso_time=self.since_iso_time, 
            to_iso_time=self.to_iso_time
        )
        
        fields = self.extra_args.fields
        if "content" not in fields:
            fields.append("content")
        self.query_repository.set_fields(
            fields=fields
        )
        self.query_repository.set_match_by_field(field="content")
        self.query_repository.set_filters(
            filters=self.extra_args.model_dump()
        )
        self.query_repository.set_order(field="@timestamp", order="desc")
        self.query_repository.set_order(field="created_at", order="desc")

        ### SEARCH DOCUMENTS ###
        documents_list = await self.es_repository.get_paginated_data(query = self.query_repository, index_pattern=self.index_pattern)

        ### MAKE CLASSIFICATION ###
        predictions_list = await self.llm_repository.apply_prompt_classification(prompt=self.prompt, task_key=self.task_key, docs_list=documents_list)
        

        ### UPDATE DOCUMENTS ###
        self.es_repository.update_documents_bulk(documents_list, predictions_list, self.update_field)
        #CAMPOS QUE ESPERA EL UPDATE Y QUE TENEMOS QUE TRAERNOS:
        # es_index_list: List[str], ¿LISTA DE STRINGS? ESTAMOS MANEJANDO UN SÓLO INDEX EN PPIO
        # doc_id_list: List[str], ¿HAY QUE TRAERSE LOS IDS DE LOS DOCUMENTOS EXPLICITAMENTE?
        # data_to_update: List[Dict], {update_field: prediction}

        ### REPORT TO WORKER ###
        return 