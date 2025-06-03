from abc import ABC, abstractmethod
from typing import List, NamedTuple, Dict, Tuple
import numpy as np
import pandas as pd
from V2.api.dtos.common_dto import BaseDocument


# Estructura de datos cruda para modelado de tópicos
class RawTopicAnalysis(NamedTuple):
    reduced_embeddings: np.ndarray
    topics_over_time: pd.DataFrame
    doc_info: pd.DataFrame
    topics_dict: Dict[int, List[Tuple[str, float]]]
    num_topics: int

class TopicsModellingServiceRepositoryInterface(ABC):
    @abstractmethod
    async def get_raw_analysis(
        self,
        documents: List[BaseDocument],
        max_topics: int = 8,
    ) -> RawTopicAnalysis:
        """
        Ejecuta la fase de modelado de tópicos y devuelve un RawTopicAnalysis
        con embeddings reducidos, evolución temporal, información de documentos,
        diccionario de tópicos y número de tópicos.
        """
        pass