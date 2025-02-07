import logging
from fastapi import HTTPException
from services.elasticsearch_service import ElasticsearchService
from api.config.secrets import ELASTIC_PSW, ELASTIC_USR, ELASTIC_PRT, ELASTIC_CLUSTER

def get_elasticsearch_client():
    try:
        return ElasticsearchService(
                                    elasticsearch_prt=ELASTIC_PRT,
                                    elasticsearch_usr=ELASTIC_USR,
                                    elasticsearch_psw=ELASTIC_PSW,
                                    elasticsearch_cluster=ELASTIC_CLUSTER)
    except ValueError as error:
        logging.error(error)
        raise HTTPException(status_code=500,
                            detail="Error while connecting to Elasticsearch")
