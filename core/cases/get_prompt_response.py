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
            prompt: str
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

    async def __call__(self) -> LLMClassificationResponse:
        ### CREATE QUERY ###


        ### SEARCH DOCUMENTS ###
        
        
        ### MAKE CLASSIFICATION ###
        

        ### UPDATE DOCUMENTS ###
        return 