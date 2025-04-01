from core.objects.document import Document
from services.elasticsearch_service import ElasticsearchService
from core.repositories.query_repository import Query
from api.config.logger import logger
import typing
from collections import defaultdict
from typing import List, Dict

class ElasticsearchRepository:

    def __init__(self, elasticsearch_service: ElasticsearchService, page_size: int = 1000):
        self.elasticsearch_service = elasticsearch_service
        self.page_size = int(page_size)

    ### SEARCH METHODS ###

    async def get_vectorized_search_data(self, index_pattern: str, query: Query, max_ndocs: int) -> typing.Dict:
        """
        Ejecuta una consulta KNN usando el método run_knn_query del servicio.
        """
        # Aquí usamos query.body para enviar el cuerpo de la consulta.
        response = await self.elasticsearch_service.run_knn_query(
            index_pattern=index_pattern,
            query=query.body,
            size=max_ndocs,
        )
        return response

    async def get_aggs_data(self, index_pattern: str, query: Query) -> typing.Dict:
        """
            retrieve the aggregations keywords and number of documents for each keyword
        """
        query.set_size(0)
        response = await self.elasticsearch_service.run_search_query(
            index_pattern=index_pattern,
            query=query.body
        )

        aggs_data = defaultdict(dict)
        for agg_name, agg_result in response.aggregations.items():
            aggs_data[agg_name] = {
                item["key"].lower(): aggs_data[agg_name].get(item["key"].lower(), 0) + item["doc_count"]
                for item in agg_result["buckets"] if item["key"]
            }
        return dict(aggs_data)
    
    async def get_aggs(self, index_pattern: str, query: Query) -> typing.Dict:
        """
            return the whole aggregations response
        """
        query.set_size(0)
        response = await self.elasticsearch_service.run_search_query(
            index_pattern=index_pattern,
            query=query.body
        )
    
        return response.aggregations

    async def get_index_data(self, index_pattern: str, body: dict ) -> typing.Tuple[typing.List[Document], typing.List]:
        search_results = await self.elasticsearch_service.run_search_query(
            index_pattern=index_pattern, query=body)
        if not search_results.hits:
            return ([], [])
        documents = [
            Document(
                **doc
            )
            for doc in search_results.hits
        ]
        return documents, search_results.last_sort_id
    
    async def get_paginated_data(self, index_pattern: str, query: Query, max_ndocs: int = None) -> typing.List[Document]:
        total_hits = []
        last_sort = []
        i = 1
        while True:
            remaining_docs = max_ndocs - len(total_hits) if max_ndocs else self.page_size

            if remaining_docs <= 0:
                break  # Stop searching when we reach max_ndocs

            page_size = min(self.page_size, remaining_docs)  # Adjust page size dynamically
            query.set_size(page_size)

            if last_sort:
                query.set_search_after(last_sort)

            es_response = await self.elasticsearch_service.run_search_query(
                index_pattern=index_pattern, 
                query=query.body
            )
            hits = es_response.hits
            logger.info(f"{len(hits)} documents brought in the page number {i} from the index: {index_pattern}") 
            i+=1

            if not hits:
                logger.info(f"No documents found for index {index_pattern}")
                break
            
            last_sort = hits[-1]["sort"]
            hits_data = []
            for hit in hits:
                flat_hit = {'_index': hit['_index'], '_id': hit['_id']}
                flat_hit.update(hit['_source'])
                hits_data.append(flat_hit)
            total_hits.extend(hits_data)

            if len(hits) < self.page_size:
                break  # Stop searching when we reach the end of the index

        documents = [
            Document(
                **doc
            )
            for doc in total_hits
        ]
        return documents
    
    async def update_documents_bulk(
        self,
        es_index_list: List[str],
        doc_id_list: List[str],
        data_to_update: List[Dict],
        bulk_method: int = 1,
        bulk_size: int = 500):
        
        is_successful = await self.elasticsearch_service.bulk_update(
            es_index_list=es_index_list,
            doc_id_list=doc_id_list,
            data_to_update=data_to_update,
            chunk_size=bulk_size
         )
    async def close_client(self):
        response = await self.elasticsearch_service.close()
        return response
