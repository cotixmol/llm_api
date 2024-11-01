import logging
from fastapi import HTTPException
from services.elasticsearch_service import ElasticsearchService
from api.config.secrets import ELASTIC_PSW, ELASTIC_USR, ELASTIC_PRT, ELASTIC_IP




def get_elasticsearch_client():
    try:
        return ElasticsearchService(elasticsearch_ip=ELASTIC_IP,
                                    elasticsearch_prt=ELASTIC_PRT,
                                    elasticsearch_usr=ELASTIC_USR,
                                    elasticsearch_psw=ELASTIC_PSW)
    except ValueError as error:
        logging.error(error)
        raise HTTPException(status_code=500,
                            detail="Error while connecting to Elasticsearch")
