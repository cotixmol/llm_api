import re
import numpy as np
from V2.core.interfaces.services.topics_modelling_service_repository_interface import (
    TopicsModellingServiceRepositoryInterface,
)
from typing import Tuple, List, Dict
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
from utils.constants import (
    NLTK_SPANISH_STOPWORDS,
    CUSTOM_STOPWORDS,
)
from utils.logger import logger
from bertopic.representation import MaximalMarginalRelevance
from bertopic.vectorizers import ClassTfidfTransformer
from bertopic.dimensionality import BaseDimensionalityReduction
from bertopic import BERTopic
from V2.api.dtos.common_dto import BaseDocument


class BertopicServiceRepositoryV2(TopicsModellingServiceRepositoryInterface):
    def __init__(
        self,
        top_n_words: int = 20,
        n_gram_range: Tuple = (1, 3),
        nr_topics: str = "auto",
        language: str = "Spanish",
        calculate_probabilities: bool = False,
    ) -> None:
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
                umap_model=BaseDimensionalityReduction(),  # Different here from the init
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
            raise Exception(error)

    def get_topics(
        self, documents: List[BaseDocument], max_topics: int = 8
    ) -> List[dict]:

        created_at, content, embeddings = self.__prepare_data(documents)

        self.hdbscan_model = self.__get_hdbscan_model(len(content))
        self.model.hdbscan_model = self.hdbscan_model  # tell BERTopic

        self.__fit_model(content, embeddings)

        topics_over_time = self.__calculate_topics(content, created_at)
        doc_info = self.model.get_document_info(content)

        topics_dict = self.__extract_topic_dict()
        num_topics = min(max_topics, len(topics_dict) - 1)

        #   ↓―― build the plain-dict payload expected by upper layers
        result: List[dict] = []
        for tid in range(num_topics):
            words = topics_dict.get(tid, [])[: self.top_n_words]
            result.append(
                {
                    "topic_id": tid,
                    "keywords": [w for w, _ in words],
                    "keyword_scores": words,
                    "documents": self.__top_documents(doc_info, tid),
                    "timeline": topics_over_time[topics_over_time["Topic"] == tid],
                }
            )
        return result

    def __reduce_embeddings(self, embeddings_np: np.ndarray) -> np.ndarray:
        logger.info(f"Embeddings shape: {embeddings_np.shape}")
        return self.umap_model.fit_transform(embeddings_np)

    def __extract_topic_dict(self) -> Dict[int, List[Tuple[str, float]]]:
        """Returns {topic_id: [(word, weight), ...]}."""
        return self.model.get_topics() or {}

    def __top_documents(self, doc_info_df, topic_id: int, k: int = 5) -> List[str]:
        return (
            doc_info_df[doc_info_df["Topic"] == topic_id]
            .sort_values("Probability", ascending=False)["Document"]
            .head(k)
            .tolist()
        )

    def __prepare_data(
        self, documents: List[BaseDocument]
    ) -> Tuple[List[str], List[str], List[List[float]]]:
        content = []
        embeddings = []
        created_at = []

        for doc in documents:
            doc_content = re.sub(r"https?://[^\s]+|www\.[^\s]+", "", doc.content)
            doc_embedding = doc.metadata.get("embedding")
            doc_created_at = doc.metadata.get("created_at")
            if not doc_content or not doc_embedding:
                continue

            content.append(doc_content)
            embeddings.append(doc_embedding)
            created_at.append(doc_created_at.strftime("%Y-%m-%dT%H:%M:%S"))

        if not content or not embeddings:
            raise ValueError("No valid documents found to calculate topics")

        return created_at, content, embeddings

    def __get_ctidf_model(self):
        return ClassTfidfTransformer(reduce_frequent_words=True)

    def __get_vectorizer_model(self):
        stopwords = NLTK_SPANISH_STOPWORDS + CUSTOM_STOPWORDS
        return CountVectorizer(ngram_range=(1, 2), stop_words=stopwords, min_df=0.01)

    def __get_representation_model(self):
        return MaximalMarginalRelevance(diversity=0.9)

    def __get_umap_model(self):
        umap_model = UMAP(n_neighbors=15, n_components=2, min_dist=0.0, metric="cosine")
        return umap_model

    def __get_hdbscan_model(self, n_docs: int | None = None):
        if n_docs is None:
            n = 10
        elif n_docs < 2_000:
            n = 10
        elif n_docs < 10_000:
            n = 40
        else:
            n = 80

        return HDBSCAN(
            min_cluster_size=n,
            min_samples=n,
            metric="euclidean",
            cluster_selection_method="eom",
            gen_min_span_tree=True,
            prediction_data=True,
        )

    def __fit_model(
        self,
        content_list: List[str],
        embeddings_list: List[List[float]],
    ):
        embeddings_np = np.array(embeddings_list)
        logger.info(f"Embeddings shape: {embeddings_np.shape}")
        # embeddings_np = normalize(embeddings_np)
        reduced_embeddings = self.umap_model.fit_transform(embeddings_np)
        logger.info(f"Reduced embeddings shape: {reduced_embeddings.shape}")
        logger.info(f"reduce embeddings: {len(reduced_embeddings)}")
        logger.info(f"content_list: {len(content_list)}")
        try:
            self.model.fit_transform(content_list, reduced_embeddings)
        except Exception as error:
            logger.warning(f"An error occurred during topic calculation: {error}")
            raise Exception(error)
        return reduced_embeddings

    def __calculate_topics(self, content_list: List[str], created_at_list: List[str]):
        return self.model.topics_over_time(
            docs=content_list,
            timestamps=created_at_list,
            nr_bins=20,
            datetime_format="%Y-%m-%dT%H:%M:%S",
        )
