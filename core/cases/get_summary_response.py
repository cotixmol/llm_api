from api.config.logger import logger
from api.dtos.responses_dtos import LLMSummaryResponse
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from core.repositories.query_repository import Query
from core.repositories.llm_repository import LLMRepository
from services.elasticsearch_service import ElasticsearchException
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
            batch_size: int,
            summary_field: str = None,
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
        self.batch_size = batch_size

    async def __call__(self) -> LLMSummaryResponse:
        ### CREATE QUERY ###
        self.query_repository.set_date_range(
            since_iso_time=self.since_iso_time, 
            to_iso_time=self.to_iso_time
        )
        
        fields = self.extra_args.fields

        # fields necessary to process the document
        if "content" not in fields:
            fields.append("content")
        if "interactions" not in fields:
            fields.append("interactions")

        #document needs to have content to be processed
        self.query_repository.set_match_by_field(field="content")
            
        if isinstance(self.query, str):   
            self.query_repository.set_query_string(query_string=f'(NOT category.keyword: "Streaming") AND (NOT content_type.keyword: "Repost") AND ({self.query})')
        else:
            self.query_repository.set_query_string(query_string='(NOT category.keyword: "Streaming") AND (NOT content_type.keyword: "Repost")')

        self.query_repository.set_filters(
            filters=self.extra_args.model_dump()
        )

        try:
            ### SEARCH DOCUMENTS ###
            if self.summary_field:
                #add summary_field to fields if not already in present
                if self.summary_field not in fields:
                    fields.append(self.summary_field)

                #if summary field set match by field
                self.query_repository.set_match_by_field(field=self.summary_field)

                #if summary field set custom aggregation to get top documents for each category
                self.query_repository.set_custom_agg(
                    {
                        "terms": {
                            "field": f"{self.summary_field}.keyword",
                            "size": 100
                        },
                        "aggs": {
                            "top_docs": {
                                "top_hits": {
                                    "sort": [
                                        {
                                            "interactions": { 
                                                "order": "desc",
                                                "unmapped_type": "long"
                                            }
                                        }
                                    ],
                                    "_source": {
                                        "includes": fields
                                    },
                                }
                            }
                        }
                    },
                    name="top_categories_hits"
                )
                response = await self.es_repository.get_aggs(query = self.query_repository, index_pattern=self.index_pattern)
            else:
                #if not summary field set order of documents by interactions
                self.query_repository.set_sort("interactions", {
                                                                    "order": "desc", 
                                                                    "unmapped_type": "long"
                                                                }) 
                self.query_repository.set_sort("@timestamp", {"order": "desc"})
                self.query_repository.set_sort("created_at", {"order": "desc"})

                self.query_repository.set_fields(fields=fields)

                response = await self.es_repository.get_paginated_data(
                                                    query = self.query_repository, 
                                                    index_pattern=self.index_pattern, 
                                                    max_ndocs=self.max_ndocs)
                if not response:
                    raise ElasticsearchException(f"No documents found for index pattern: {self.index_pattern}")
            
            ### MAKE PREDICTION ###
            match (self.summary_field, self.query):
                case (str() as summary_field, _):  #Entra si summary_field es un str, sin importar query
                    response_dict = await self.llm_repository.apply_prompt_categories_summary(
                        aggs=response, prompt_template=self.prompt, summary_field=summary_field, batch_size=self.batch_size
                    )
                case (None, str() as query):  #Entra solo si summary_field es None y query es un str
                    response_dict = await self.llm_repository.apply_prompt_query_summary(
                        docs=response, prompt_template=self.prompt, query=query
                    )
                case (None, None):  #Entra solo si ambos son None
                    response_dict = await self.llm_repository.apply_prompt_summary( 
                        docs=response, prompt_template=self.prompt
                    )


        finally:
            ### CLOSE CLIENT ###
            await self.es_repository.close_client()
            logger.info(f"Client closed")

        return LLMSummaryResponse(response=response_dict)