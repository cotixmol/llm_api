from fastapi import Depends, HTTPException
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from services.elasticsearch_service import ElasticsearchService
from factories.services.elasticsearch_client_factory import get_elasticsearch_client
from api.config.secrets import ELASTIC_PAGE_SIZE

def get_elasticsearch_repository(es_service: ElasticsearchService = Depends(get_elasticsearch_client)):
    try:
        return ElasticsearchRepository(elasticsearch_service=es_service, page_size=ELASTIC_PAGE_SIZE)
    except ValueError:
        raise HTTPException(status_code=500, detail="Error while connecting to Elasticsearch")
