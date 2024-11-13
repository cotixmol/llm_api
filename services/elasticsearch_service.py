# services/elasticsearch_service.py
import typing
from elasticsearch import Elasticsearch, NotFoundError, BadRequestError
from api.dtos.elasticsearch_dtos import IndexStatus, SearchResponse
import logging


class ElasticsearchException(Exception):
    pass

class ElasticsearchService:

    def __init__(self, elasticsearch_ip: str, elasticsearch_prt: str,
                 elasticsearch_usr: str, elasticsearch_psw: str) -> None:
        self.client = Elasticsearch(
            hosts=[f"https://{elasticsearch_ip}:{elasticsearch_prt}"],
            basic_auth=(elasticsearch_usr, elasticsearch_psw),
            verify_certs=False)

    async def get_indexes_information(
            self, index_patern: str) -> typing.List[IndexStatus]:

        indexes_status = self.client.cat.indices(
            index=index_patern,
            bytes='b',
            format="json"
        )
        return [
            IndexStatus(health=index["health"],
                        index=index["index"],
                        docs_count=index["docs.count"],
                        pri_store_size=index["pri.store.size"])
            for index in indexes_status
        ]

    async def open_pit(self, index_pattern: str, keep: str) -> str:
        try:
            response = self.client.open_point_in_time(index=index_pattern, keep_alive=keep)
            logging.info(f"PIT opened for index_pattern {index_pattern}")
        except NotFoundError as not_found:
            logging.error(f"ElasticService error: {not_found}")
            raise ElasticsearchException(f"ElasticService error: {not_found}")
        return response["id"] if response else None
    
    async def close_pit(self, pit_id: str) -> None:
        try:
            self.client.close_point_in_time(id=pit_id)
            logging.info(f"PIT closed")
        except NotFoundError as not_found:
            logging.error(f"ElasticService error: {not_found}")
            raise ElasticsearchException(f"ElasticService error: {not_found}")

    async def run_pit_search_query(
        self,
        query: dict,
    ) -> SearchResponse:
        """Advance way to get documents and/or aggregation using elastic queries. Use PIT to avoid data inconsistency.

        Args:
            query (dict): body from Query repository, the Query must have a PIT object with the ID.

        Raises:
            ElasticsearchException: generic exception with details

        Returns:
            SearchResponse: object with hits and aggregations
        """
        try:
            search_results = self.client.search(body=query)
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
        last_sort_id = search_results["hits"]["hits"][-1].get("sort", []) if hits else []

        return SearchResponse(hits=hits, last_sort_id=last_sort_id, total_hits=total_hits)

    async def run_search_query(
        self,
        index_pattern: str,
        query: dict,
    ) -> SearchResponse:
        try:
            search_results = self.client.search(index=index_pattern, body=query, request_timeout=10)
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
        last_sort_id = search_results["hits"]["hits"][-1].get("sort", []) if hits else []
        aggs = {}
        if query.get("aggs"):
            if "aggregations" not in search_results.keys():
                raise ElasticsearchException(f"ElasticService error: Bad query. Check that the index pattern is correct")
            aggs = search_results['aggregations']
        return SearchResponse(hits=hits, aggregations=aggs, last_sort_id=last_sort_id, total_hits=total_hits)
