from typing import List, Tuple, Dict
from api.config.logger import logger
from api.dtos.responses_dtos import LLMSummaryResponse
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from core.repositories.query_repository import Query
from core.repositories.llm_repository import LLMRepository
from api.config.secrets import ELASTIC_PAGE_SIZE
import iso8601

import re

_N_DOCS = 0

class GetSummaryResponseCase:
    def __init__(
            self,
            es_repository: ElasticsearchRepository,
            query_repository: Query,
            llm_repository: LLMRepository,
            index_pattern: str,
            since_date: str,
            to_date: str,
            extra_args: dict,
            prompt: dict, 
            max_ndocs: int,
            summary_field: str,
            query: str = None,            
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
        self.max_ndocs = max_ndocs
        self.query = query
        self.summary_field = summary_field

    async def __call__(self) -> LLMSummaryResponse:
        ### CREATE QUERY ###
        self.query_repository.set_date_range(
            since_iso_time=self.since_iso_time, 
            to_iso_time=self.to_iso_time
        )
        
        fields = self.extra_args.fields
        if "content" not in fields:
            fields.append("content")
        if self.summary_field not in fields:
            fields.append(self.summary_field)
        self.query_repository.set_fields(
            fields=fields
        )
        self.query_repository.set_match_by_field(field="content")
        self.query_repository.set_match_by_field(field=self.summary_field)
        if self.query is not None:
            self.query_repository.set_query_string(query_string=f'(NOT category.keyword: "Streaming") AND (content_type.keyword: ("Post" OR "tweet" OR "New" OR "videos" OR "shorts")) AND {self.query}') #Definir
        else:
            self.query_repository.set_query_string(query_string='(NOT category.keyword: "Streaming") AND (content_type.keyword: ("Post" OR "tweet" OR "New" OR "videos" OR "shorts"))')
        self.query_repository.set_filters(
            filters=self.extra_args.model_dump()
        )
        PAGE_SIZE = min(int(ELASTIC_PAGE_SIZE), int(self.max_ndocs)) if self.max_ndocs else int(ELASTIC_PAGE_SIZE)
        self.query_repository.set_size(PAGE_SIZE)
        self.query_repository.set_order(field="interactions", order="desc")
        self.query_repository.set_order(field="@timestamp", order="desc")
        self.query_repository.set_order(field="created_at", order="desc")

        try:
            ### SEARCH DOCUMENTS ###
            hits = await self.es_repository.get_paginated_data(query = self.query_repository, index_pattern=self.index_pattern)
            print("HITS", hits)
            print("Query", self.query_repository.body)
            ### MAKE PREDICTION ###
            response_dict = await self.llm_repository.apply_prompt_summary(docs=hits, prompt_template=self.prompt, summary_field=self.summary_field)
            
            print(response_dict)

        finally:
            ### CLOSE CLIENT ###
            await self.es_repository.close_client()
            logger.info(f"Client closed")

        return LLMSummaryResponse(response=response_dict)