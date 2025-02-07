import logging
from fastapi import HTTPException
from services.elasticsearch_service import ElasticsearchService
from api.config.secrets import settings as s 

def get_elasticsearch_client():
    try:
        return ElasticsearchService(
                                    elasticsearch_prt=s.ELASTIC_PRT,
                                    elasticsearch_usr=s.ELASTIC_USR,
                                    elasticsearch_psw=s.ELASTIC_PSW,
                                    elasticsearch_cluster=s.ELASTIC_CLUSTER)
    except ValueError as error:
        logging.error(error)
        raise HTTPException(status_code=500,
                            detail="Error while connecting to Elasticsearch")
