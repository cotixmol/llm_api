# services/elasticsearch_service.py
import typing
from elasticsearch import Elasticsearch, NotFoundError, BadRequestError, ConnectionTimeout
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
            retry_on_timeout=True,
            max_retries=5,
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

    async def run_search_query(
        self,
        index_pattern: str,
        query: dict,
    ) -> SearchResponse:
        try:
            search_results = self.client.options(request_timeout=10).search(index=index_pattern, body=query)
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
