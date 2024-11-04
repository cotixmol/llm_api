import logging
from typing import List, Tuple, Dict
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from core.repositories.query_repository import Query
import iso8601
from core.repositories.bertopic_repository import BertopicRepository
from core.objects.document import Document
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.representation import MaximalMarginalRelevance
from bertopic.vectorizers import ClassTfidfTransformer
# from umap import UMAP
from sklearn.decomposition import PCA
# from hdbscan import HDBSCAN
from cuml.cluster import HDBSCAN
from cuml.manifold import UMAP
import nltk
from nltk.corpus import stopwords as sp
import numpy as np

CUSTOM_STOPWORDS = ['http', "link", "bio", 'https', 'amp', "va", 'com', "si", "mas", "anos", "ano", "vos", "RT", "usted", "ustedes", "tenes", "tambien", "tan", "sos", "solo"]
PAGE_SIZE = 500
_N_DOCS = 0

class GetTopicChartsCase:
    def __init__(
            self,
            es_repository: ElasticsearchRepository,
            query_repository: Query,
            index_pattern: str,
            since_date: str,
            to_date: str,
            extra_args: dict
    ):
        since_iso_time = iso8601.parse_date(since_date).isoformat()
        to_iso_time = iso8601.parse_date(to_date).isoformat()
        self.query_repository = query_repository      
        self.es_repository = es_repository
        self.index_pattern = index_pattern
        self.since_iso_time = since_iso_time
        self.to_iso_time = to_iso_time
        self.extra_args = extra_args

    async def __call__(self) -> Tuple[Dict, int]:
        self.query_repository.set_date_range(
            since_iso_time=self.since_iso_time, to_iso_time=self.to_iso_time
        )
        fields = self.extra_args.fields
        if "embedding" not in fields:
            fields.append("embedding")
        self.query_repository.set_fields(
            fields=fields
        )
        self.query_repository.set_match_by_field(field="embedding")
        self.query_repository.set_filters(
            filters=self.extra_args.model_dump()
        )
        self.query_repository.set_size(size=PAGE_SIZE)
        self.query_repository.set_order(field="@timestamp", order="desc")
        package_size = PAGE_SIZE
        documents_list = []
        page_number = 0

        while package_size >= PAGE_SIZE:
            page_number += 1
            documents, last_sort_id = await self.es_repository.get_index_data(
                index_pattern=self.index_pattern,
                body=self.query_repository.body
            )
            package_size = len(documents)
            documents_list.extend(documents)
            logging.info(f"Reading {len(documents)} documents from {page_number} pages")
            self.query_repository.set_search_after(search_after=last_sort_id)
        print(f"{len(documents)} documents founded")
        logging.info(f"Found {len(documents_list)} in {page_number} pages")
        created_at_list, content_list, embedding_list = self.__prepare_data(documents_list)

        if not all((content_list, embedding_list)):
            logging.warning("There are no documents to calculate topics")
            return {"topics": {}}

        bertopic_repository = BertopicRepository(
            umap_model=self.__get_umap_model(),
            hdbscan_model=self.__get_hdbscan_model(len(content_list)),
            vectorizer_model=self.__get_vectorizer_model(),
            representation_model=self.__get_representation_model(),
            ctfidf_model=self.__get_ctidf_model(),
            top_n_words=20,
            n_gram_range=(1,3),
            nr_topics="auto",
            language="Spanish",
            calculate_probabilities=False
        )

        
        topics = bertopic_repository.get_topics(
            created_at_list=created_at_list,
            content_list=content_list,
            embeddings_list=embedding_list
        )
        return topics, len(embedding_list)
    
    def __prepare_data(self, documents: List[Document]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        content = []
        embeddings = []
        created_at=[]
        for doc in documents:
            doc_content = doc.content
            doc_embedding = doc.embedding
            doc_created_at = doc.created_at
            if not doc_content or not doc_embedding:
                print(f"skiperd document", doc)
                continue
            content.append(doc_content)
            embeddings.append(doc_embedding)
            created_at.append(doc_created_at.strftime(format="%Y-%m-%dT%H:%M:%S"))

        return created_at, content, embeddings
    

    def __get_umap_model(self):    
        umap_model = UMAP(
            n_neighbors=15,
            n_components=2,
            min_dist=0.0,
            metric="cosine"
        )
        return umap_model

        
    def __get_hdbscan_model(self, n_docs: int):

        if n_docs < 2000:
            n=10
        elif n_docs < 10000:
            n=40
        else:
            n=80

        hdbscan_model = HDBSCAN(min_cluster_size=n, min_samples=n,
        metric='euclidean',
        cluster_selection_method='eom',
         gen_min_span_tree=True,
         prediction_data=True)

        return hdbscan_model
    
    def __get_vectorizer_model(self):
        nltk.download('stopwords')
        stopwords = list(sp.words('spanish')) + CUSTOM_STOPWORDS
        return CountVectorizer(ngram_range=(1, 2), stop_words=stopwords, min_df=0.01) 
    
    def __get_representation_model(self):
        return MaximalMarginalRelevance(diversity=0.9)
    
    def __get_ctidf_model(self):
        return ClassTfidfTransformer(reduce_frequent_words=True)

