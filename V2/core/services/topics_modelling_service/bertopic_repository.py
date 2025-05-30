from typing import List, Dict, Tuple, NamedTuple
import re
import numpy as np
import pandas as pd
from collections import namedtuple
from umap import UMAP
from hdbscan import HDBSCAN
from bertopic import BERTopic
from bertopic.vectorizers import ClassTfidfTransformer
from bertopic.representation import MaximalMarginalRelevance
from bertopic.dimensionality import BaseDimensionalityReduction
from V2.utils.logger import logger
from sklearn.feature_extraction.text import CountVectorizer
from V2.api.dtos.common_dto import BaseDocument
from V2.core.interfaces.services.topics_modelling_service_repository_interface import (
    TopicsModellingServiceRepositoryInterface,
    RawTopicAnalysis
)


class BertopicServiceRepositoryV2(TopicsModellingServiceRepositoryInterface):
    def __init__(
        self,
        top_n_words: int = 20,
        n_gram_range: Tuple[int, int] = (1, 3),
        nr_topics: str = "auto",
        language: str = "Spanish",
        calculate_probabilities: bool = False,
    ) -> None:
        # Initialize UMAP, HDBSCAN, vectorizer and BERTopic model
        self.umap_model = self.__get_umap_model()
        self.hdbscan_model = self.__get_hdbscan_model()
        self.vectorizer_model = self.__get_vectorizer_model()
        self.representation_model = self.__get_representation_model()
        self.ctfidf_model = self.__get_ctidf_model()
        self.top_n_words = top_n_words
        self.n_gram_range = n_gram_range
        self.nr_topics = nr_topics
        self.language = language
        self.calculate_probabilities = calculate_probabilities

        try:
            self.model = BERTopic(
                umap_model=BaseDimensionalityReduction(),
                hdbscan_model=self.hdbscan_model,
                vectorizer_model=self.vectorizer_model,
                representation_model=self.representation_model,
                ctfidf_model=self.ctfidf_model,
                top_n_words=self.top_n_words,
                n_gram_range=self.n_gram_range,
                nr_topics=self.nr_topics,
                language=self.language,
                calculate_probabilities=self.calculate_probabilities,
                verbose=True,
            )
        except Exception as error:
            raise Exception(f"Failed to initialize BERTopic: {error}")

    async def get_raw_analysis(
        self,
        documents: List[BaseDocument],
        max_topics: int = 8,
    ) -> RawTopicAnalysis:
        """
        Ejecuta solo la fase de modelado de tópicos y devuelve datos puros:
        - reduced_embeddings: np.ndarray (n_docs x 2)
        - topics_over_time: pd.DataFrame
        - doc_info: pd.DataFrame
        - topics_dict: Dict[int, List[Tuple[str,float]]]
        - num_topics: número efectivo de tópicos a exponer
        """
        # 1) Preparar datos
        created_at, content, embeddings = self.__prepare_data(documents)

        # 2) Ajustar modelo y reducir embeddings
        reduced_embeddings = self.__setup_and_fit_model(content, embeddings)

        # 3) Calcular análisis de tópicos puros
        topics_over_time, doc_info, topics_dict, num_topics = self.__calculate_topic_analysis(
            content, created_at, max_topics
        )

        return RawTopicAnalysis(
            reduced_embeddings=reduced_embeddings,
            topics_over_time=topics_over_time,
            doc_info=doc_info,
            topics_dict=topics_dict,
            num_topics=num_topics,
        )

    # --- Métodos auxiliares privados ---

    def __prepare_data(
        self, documents: List[BaseDocument]
    ) -> Tuple[List[str], List[str], List[List[float]]]:
        content, embeddings, created_at = [], [], []
        for doc in documents:
            text = re.sub(r"https?://[^\s]+|www\.[^\s]+", "", doc.content)
            emb = doc.metadata.get("embedding")
            ts = doc.metadata.get("created_at")
            if not text or emb is None:
                continue
            content.append(text)
            embeddings.append(emb)
            # Normalizar timestamp
            if isinstance(ts, str):
                ts_clean = ts.rstrip("Z").split("+")[0]
                created_at.append(ts_clean)
            elif hasattr(ts, "strftime"):
                created_at.append(ts.strftime("%Y-%m-%dT%H:%M:%S"))
            else:
                logger.warning(f"Skipping doc with invalid timestamp: {ts}")
        if not content:
            raise ValueError("No valid documents found for topic modeling.")
        return created_at, content, embeddings

    def __setup_and_fit_model(
        self, content: List[str], embeddings: List[List[float]]
    ) -> np.ndarray:
        # Re-calcular HDBSCAN de acuerdo al tamaño de corpus
        self.hdbscan_model = self.__get_hdbscan_model(len(content))
        self.model.hdbscan_model = self.hdbscan_model

        # Ajustar UMAP + BERTopic
        embeddings_np = np.array(embeddings)
        reduced = self.umap_model.fit_transform(embeddings_np)
        try:
            self.model.fit_transform(content, reduced)
        except Exception as e:
            logger.warning(f"Error during BERTopic fit: {e}")
            raise Exception(f"Topic modeling failed: {e}")
        return reduced

    def __calculate_topic_analysis(
        self, content: List[str], created_at: List[str], max_topics: int
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[int, List[Tuple[str, float]]], int]:
        # Evolución temporal
        topics_over_time = self.model.topics_over_time(
            docs=content,
            timestamps=created_at,
            nr_bins=20,
            datetime_format="%Y-%m-%dT%H:%M:%S",
        )
        # Información por documento
        doc_info = self.model.get_document_info(content)
        # Diccionario de tópicos {topic_id: [(keyword, score), ...]}
        topics_dict = self.model.get_topics() or {}
        num_topics = min(max_topics, len(topics_dict) - 1)
        return topics_over_time, doc_info, topics_dict, num_topics

    def __get_umap_model(self) -> UMAP:
        return UMAP(n_neighbors=15, n_components=2, min_dist=0.0, metric="cosine")

    def __get_hdbscan_model(self, n_docs: int = None) -> HDBSCAN:
        n = 10 if n_docs is None or n_docs < 2000 else 40 if n_docs < 10000 else 80
        return HDBSCAN(
            min_cluster_size=n,
            min_samples=n,
            metric="euclidean",
            cluster_selection_method="eom",
            gen_min_span_tree=True,
            prediction_data=True,
        )

    def __get_vectorizer_model(self) -> CountVectorizer:
        from V2.core.services.topics_modelling_service.utils.constants import (
            NLTK_SPANISH_STOPWORDS,
            CUSTOM_STOPWORDS,
        )
        stopwords = NLTK_SPANISH_STOPWORDS + CUSTOM_STOPWORDS
        return CountVectorizer(ngram_range=(1, 2), stop_words=stopwords, min_df=0.01)

    def __get_ctidf_model(self) -> ClassTfidfTransformer:
        return ClassTfidfTransformer(reduce_frequent_words=True)

    def __get_representation_model(self) -> MaximalMarginalRelevance:
        return MaximalMarginalRelevance(diversity=0.9)
