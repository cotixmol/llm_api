from typing import List, Dict
from elasticsearch import NotFoundError, BadRequestError, AsyncElasticsearch
from elasticsearch.helpers import async_bulk, async_streaming_bulk, parallel_bulk
from api.dtos.elasticsearch_dtos import SearchResponse
import logging


class ElasticsearchException(Exception):
    pass

class ElasticsearchService:

    def __init__(self, elasticsearch_ip: str, elasticsearch_prt: str,
                 elasticsearch_usr: str, elasticsearch_psw: str) -> None:
        self.client = AsyncElasticsearch(
            hosts=[f"https://{elasticsearch_ip}:{elasticsearch_prt}"],
            http_auth=(elasticsearch_usr, elasticsearch_psw),
            retry_on_timeout=True,
            max_retries=5,
            verify_certs=False)
            
    async def close(self) -> None:
        """Closes the Elasticsearch client."""
        response = await self.client.close()
        return response

    async def run_search_query(
        self,
        index_pattern: str,
        query: dict,
    ) -> SearchResponse:
        try:
            search_results = await self.client.options(request_timeout=10).search(index=index_pattern, body=query)
        except NotFoundError as not_found:
            logging.error(f"ElasticService error: {not_found}")
            raise ElasticsearchException(f"ElasticService error: {not_found}")
        except BadRequestError as request_error:
            logging.error(f"ElasticSearch request error: {request_error}")
            raise ElasticsearchException(f"ElasticSearch request error: {request_error}")
        
        client_errors = search_results['_shards'].get('failures')
        if client_errors:
            logging.error(f"ERROR: {client_errors}")
            raise ElasticsearchException(client_errors)
        total_hits = search_results['hits']['total']['value']
        hits = [hit['_source'] for hit in search_results['hits']['hits']]
        aggs = {}
        if query.get("aggs"):
            if "aggregations" not in search_results.keys():
                raise ElasticsearchException(f"ElasticService error: Bad query. Check that the index pattern is correct")
            aggs = search_results['aggregations']
        return SearchResponse(hits=hits, aggregations=aggs, total_hits=total_hits)
    
    async def run_helpers_bulk(
            self,
            es_index_list: List[str],
            doc_id_list: List[str],
            data_to_update: List[Dict],
            bulk_method: int = 1,
            bulk_size: int = 500):
        """toma una lista de es_id y doc_id y actualiza dentro de elastic en nuevo campo

        Args:
            es_index_list (List[str]): index column
            doc_id_list (List[str]): document id column
            data_to_update (List[dict]): list of ojects with data to update. ej: [{"token": "token_value"}]
            bulk_method (int): 0 for bulk, 1 for parallel_bulk, 2 for streaming_bulk. Defaults to 1.
            bulk_size (int): size of the bulk. Defaults to 500.
        """

        actions = [{"_op_type": "update", "_index": idx, "_id": doc_id, "doc": update_data} 
                   for idx, doc_id, update_data 
                   in zip(es_index_list, doc_id_list, data_to_update)]
        
        try:
            failures = 0            

            match bulk_method:
                case 0:
                    response = await async_bulk(client = self.client, 
                        actions = actions, 
                        chunk_size = bulk_size)
                    errors = len(response[1])
                    failures += errors
                case 1:
                    for success, info in parallel_bulk(client = self.client, 
                                        actions = actions, 
                                        chunk_size = bulk_size):
                        if not success:
                            failures += 1
                case 2:
                    async for success, info in async_streaming_bulk(client = self.client, 
                                        actions = actions, 
                                        chunk_size = bulk_size):
                        if not success:
                            failures += 1
            logging.info(f"Ingest done with {failures} failures.")
            return            
        except Exception as e:
            msg = f"An error ocurred {e}"
            raise ElasticsearchException(msg)

