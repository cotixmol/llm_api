from fastapi import HTTPException
from core.repositories.query_repository import Query


def get_query_repository():
        return Query()
