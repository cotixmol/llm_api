from typing import List, Tuple, Dict
from api.config.logger import logger
from core.repositories.elasticsearch_repository import ElasticsearchRepository
from core.repositories.query_repository import Query
from core.repositories.llm_repository import LLMRepository
import iso8601
from core.repositories.bertopic_repository import BertopicRepository, BertopicRepositoryException
from core.objects.document import Document
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.representation import MaximalMarginalRelevance
from bertopic.vectorizers import ClassTfidfTransformer
from umap import UMAP
from sklearn.decomposition import PCA
from hdbscan import HDBSCAN
#from cuml.cluster import HDBSCAN
#from cuml.manifold import UMAP
import re

CUSTOM_STOPWORDS = ["co", "rt", "dice", "min", "asi" "eh", "etc", "decis", 'http', "link", "bio", 'https', 'amp', "va", 'com', "si", "mas", "anos", "ano", "vos", "RT", "usted", "ustedes", "tenes", "tambien", "tan", "sos", "solo"]
NLTK_SPANISH_STOPWORDS = ['de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'del', 'se', 'las', 'por', 'un', 'para', 'con', 'no', 'una', 'su', 'al', 'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'este', 'sí', 'porque', 'esta', 'entre', 'cuando', 'muy', 'sin', 'sobre', 'también', 'me', 'hasta', 'hay', 'donde', 'quien', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'qué', 'unos', 'yo', 'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada', 'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo', 'nosotros', 'mi', 'mis', 'tú', 'te', 'ti', 'tu', 'tus', 'ellas', 'nosotras', 'vosotros', 'vosotras', 'os', 'mío', 'mía', 'míos', 'mías', 'tuyo', 'tuya', 'tuyos', 'tuyas', 'suyo', 'suya', 'suyos', 'suyas', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'vuestro', 'vuestra', 'vuestros', 'vuestras', 'esos', 'esas', 'estoy', 'estás', 'está', 'estamos', 'estáis', 'están', 'esté', 'estés', 'estemos', 'estéis', 'estén', 'estaré', 'estarás', 'estará', 'estaremos', 'estaréis', 'estarán', 'estaría', 'estarías', 'estaríamos', 'estaríais', 'estarían', 'estaba', 'estabas', 'estábamos', 'estabais', 'estaban', 'estuve', 'estuviste', 'estuvo', 'estuvimos', 'estuvisteis', 'estuvieron', 'estuviera', 'estuvieras', 'estuviéramos', 'estuvierais', 'estuvieran', 'estuviese', 'estuvieses', 'estuviésemos', 'estuvieseis', 'estuviesen', 'estando', 'estado', 'estada', 'estados', 'estadas', 'estad', 'he', 'has', 'ha', 'hemos', 'habéis', 'han', 'haya', 'hayas', 'hayamos', 'hayáis', 'hayan', 'habré', 'habrás', 'habrá', 'habremos', 'habréis', 'habrán', 'habría', 'habrías', 'habríamos', 'habríais', 'habrían', 'había', 'habías', 'habíamos', 'habíais', 'habían', 'hube', 'hubiste', 'hubo', 'hubimos', 'hubisteis', 'hubieron', 'hubiera', 'hubieras', 'hubiéramos', 'hubierais', 'hubieran', 'hubiese', 'hubieses', 'hubiésemos', 'hubieseis', 'hubiesen', 'habiendo', 'habido', 'habida', 'habidos', 'habidas', 'soy', 'eres', 'es', 'somos', 'sois', 'son', 'sea', 'seas', 'seamos', 'seáis', 'sean', 'seré', 'serás', 'será', 'seremos', 'seréis', 'serán', 'sería', 'serías', 'seríamos', 'seríais', 'serían', 'era', 'eras', 'éramos', 'erais', 'eran', 'fui', 'fuiste', 'fue', 'fuimos', 'fuisteis', 'fueron', 'fuera', 'fueras', 'fuéramos', 'fuerais', 'fueran', 'fuese', 'fueses', 'fuésemos', 'fueseis', 'fuesen', 'sintiendo', 'sentido', 'sentida', 'sentidos', 'sentidas', 'siente', 'sentid', 'tengo', 'tienes', 'tiene', 'tenemos', 'tenéis', 'tienen', 'tenga', 'tengas', 'tengamos', 'tengáis', 'tengan', 'tendré', 'tendrás', 'tendrá', 'tendremos', 'tendréis', 'tendrán', 'tendría', 'tendrías', 'tendríamos', 'tendríais', 'tendrían', 'tenía', 'tenías', 'teníamos', 'teníais', 'tenían', 'tuve', 'tuviste', 'tuvo', 'tuvimos', 'tuvisteis', 'tuvieron', 'tuviera', 'tuvieras', 'tuviéramos', 'tuvierais', 'tuvieran', 'tuviese', 'tuvieses', 'tuviésemos', 'tuvieseis', 'tuviesen', 'teniendo', 'tenido', 'tenida', 'tenidos', 'tenidas', 'tened']
_N_DOCS = 0

class GetTopicChartsCase:
    def __init__(
            self,
            es_repository: ElasticsearchRepository,
            query_repository: Query,
            llm_repository: LLMRepository,
            index_pattern: str,
            since_date: str,
            to_date: str,
            extra_args: dict
    ):
        since_iso_time = iso8601.parse_date(since_date).isoformat()
        to_iso_time = iso8601.parse_date(to_date).isoformat()
        self.query_repository = query_repository      
        self.es_repository = es_repository
        self.llm_repository = llm_repository
        self.index_pattern = index_pattern
        self.since_iso_time = since_iso_time
        self.to_iso_time = to_iso_time
        self.extra_args = extra_args

    async def __call__(self) -> Tuple[Dict, int]:
        ### CREATE QUERY ###
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
        self.query_repository.set_order(field="@timestamp", order="desc")
        self.query_repository.set_order(field="created_at", order="desc")


        ### SEARCH DOCUMENTS ###

        documents_list = await self.es_repository.get_paginated_data(query = self.query_repository, index_pattern=self.index_pattern)
        ### GET TOPICS ###
        created_at_list, content_list, embedding_list = self.__prepare_data(documents_list)

        if not all((content_list, embedding_list)):
            raise BertopicRepositoryException("There are no documents to calculate topics")

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
            calculate_probabilities=False,
            llm_repository=self.llm_repository
        )

        
        topics = await bertopic_repository.get_topics(
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
            doc_content = re.sub(r'https?://[^\s]+|www\.[^\s]+', "", doc.content)
            doc_embedding = doc.embedding
            doc_created_at = doc.created_at
            if not doc_content or not doc_embedding:
                print(f"skiped document", doc_content)
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
        stopwords = NLTK_SPANISH_STOPWORDS + CUSTOM_STOPWORDS
        return CountVectorizer(ngram_range=(1, 2), stop_words=stopwords, min_df=0.01) 
    
    def __get_representation_model(self):
        return MaximalMarginalRelevance(diversity=0.9)
    
    def __get_ctidf_model(self):
        return ClassTfidfTransformer(reduce_frequent_words=True)

