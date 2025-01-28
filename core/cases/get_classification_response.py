from typing import List, Tuple, Dict
from api.config.logger import logger
from api.dtos.responses_dtos import LLMClassificationResponse
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from core.repositories.query_repository import Query
from core.repositories.llm_repository import LLMRepository
from api.config.secrets import ELASTIC_PAGE_SIZE
import iso8601

import re

_N_DOCS = 0

class GetClassificationResponseCase:
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
            update_field:str,
            valid_labels: List[str],
            max_ndocs: int
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
        self.valid_labels = valid_labels
        self.max_ndocs = max_ndocs

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
        #self.query_repository.set_not_match_by_field(field=self.update_field)
        self.query_repository.set_filters(
            filters=self.extra_args.model_dump()
        )
        PAGE_SIZE = min(int(ELASTIC_PAGE_SIZE), int(self.max_ndocs)) if self.max_ndocs else int(ELASTIC_PAGE_SIZE)
        self.query_repository.set_size(PAGE_SIZE)
        self.query_repository.set_order(field="@timestamp", order="desc")
        self.query_repository.set_order(field="created_at", order="desc")
        try:
            ### SEARCH DOCUMENTS ###
            hits = await self.es_repository.get_paginated_data(query = self.query_repository, index_pattern=self.index_pattern)

            ### MAKE CLASSIFICATION ###
            predictions_dict = await self.llm_repository.apply_prompt_classification(prompt_template=self.prompt, task_key=self.task_key, docs=hits, valid_labels=self.valid_labels, update_field=self.update_field)
            
            print(predictions_dict)

            ### UPDATE DOCUMENTS ###
            await self.es_repository.update_documents_bulk(
                es_index_list=predictions_dict["es_index_list"], 
                data_to_update=predictions_dict["classification_list"],
                doc_id_list=predictions_dict["doc_id_list"]
                )
        finally:
            ### CLOSE CLIENT ###
            await self.es_repository.close_client()
            logger.info(f"Client closed")
        
        ### REPORT TO WORKER ###

        response = LLMClassificationResponse(
            total_docs=len(predictions_dict["classification_list"]),
            updated_docs=len([doc for doc in predictions_dict["classification_list"] if doc is not None])
        )

        return response