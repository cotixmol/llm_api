from typing import Dict, Any, Optional, List
from pydantic import BaseModel, model_validator
from V2.core.objects.elastic_search_object import ElasticSearchDocument
from V2.api.dtos.common_dto import Filters
from V2.api.dtos.common_dto import BaseDocument


class ClassificationRequest(BaseModel):
    index_pattern: Optional[str] = None
    since_date: Optional[str] = None
    to_date: Optional[str] = None
    filters: Optional[Filters] = None
    prompt: dict
    update_field: str
    task_key: str
    match_field: Optional[str] = None
    valid_labels: List[str]
    max_ndocs: Optional[int] = 10000
    batch_size: Optional[int] = 50
    query: Optional[str] = None
    documents: Optional[List[BaseDocument]] = None

    @model_validator(mode="after")
    def validate_data_source(self) -> "ClassificationRequest":
        has_documents = self.documents is not None
        has_search_params = all([self.index_pattern, self.since_date, self.to_date])

        if not has_documents and not has_search_params:
            raise ValueError(
                "Debe proveerse una lista de documentos (`documents`) o parámetros de búsqueda (`index_pattern`, `since_date`, `to_date`)."
            )
        
        if has_documents:
            for doc in self.documents:
                if "applied_transformations" not in doc.metadata:
                    raise ValueError(
                        "Cada documento en 'documents' debe tener 'applied_transformations' en 'metadata'."
                    )
        return self

class ClassificationResponse(BaseModel):
    total_docs: int
    updated_docs: int


class ClassificationOutput(BaseModel):
    classification: Optional[str]
    metadata: Dict[str, Any]
