import typing
import logging
from collections import defaultdict
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.representation import MaximalMarginalRelevance
import numpy as np
from cuml.manifold import UMAP
from cuml.cluster import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.vectorizers import ClassTfidfTransformer
from bertopic.dimensionality import BaseDimensionalityReduction
from core.repositories.llm_repository import LLMRepository

from core.objects.barplot import Barplot, BarPlotUnit
from core.objects.wordcloud import Word, Wordcloud
from core.objects.stackedline import StackedLine, StackedSerie
# from core.objects.timeline import Timeline
from core.objects.document import ContentText, DocumentGroup
from core.objects.pie import PieChart, PieSlice
from core.objects.topic_info import TopicInfo

class BertopicRepositoryException(Exception):
    pass


class BertopicRepository:
    def __init__(
            self,
            umap_model: UMAP,
            hdbscan_model: HDBSCAN,
            vectorizer_model: CountVectorizer,
            representation_model: MaximalMarginalRelevance,
            ctfidf_model: ClassTfidfTransformer,
            top_n_words: int,
            n_gram_range: typing.Tuple,
            nr_topics: str,
            language: str,
            calculate_probabilities: bool,
            llm_repository: LLMRepository,

    ) -> None:
        try:
            self.model = BERTopic(
                    umap_model=BaseDimensionalityReduction(),
                    hdbscan_model=hdbscan_model,
                    vectorizer_model=vectorizer_model,
                    representation_model=representation_model,
                    ctfidf_model=ctfidf_model,
                    top_n_words=top_n_words,
                    n_gram_range=n_gram_range,
                    nr_topics=nr_topics,
                    language=language,
                    calculate_probabilities=calculate_probabilities,
                    verbose=True
            )
            self.llm_repository = llm_repository
            self.umap_model = umap_model
        except Exception as error:
            raise BertopicRepositoryException(error)
 
    def __fit_model(self, content_list: typing.List[str], embeddings_list: typing.List[typing.List[float]]):
        embeddings_np = np.array(embeddings_list)
        reduced_embeddings = self.umap_model.fit_transform(embeddings_np)
        try:
            self.model.fit_transform(content_list, reduced_embeddings)
        except Exception as e:
            logging.warning(f"An error occurred during topic calculation: {e}")
            raise BertopicRepositoryException(e)
        return reduced_embeddings

    def __calculate_topics(self, content_list: typing.List[str], created_at_list: typing.List[str]):
        return self.model.topics_over_time(docs=content_list, timestamps=created_at_list, nr_bins=20, datetime_format="%Y-%m-%dT%H:%M:%S")

    def get_topics(self,
    created_at_list: typing.List[str],
    content_list: typing.List[str],
    embeddings_list: typing.List[typing.List[float]]
    ) -> typing.Dict:
        MAX_TOPICS = 8
        MAX_WORDS = 10
        MAX_DOCS = 5
        reduced_embeddings = self.__fit_model(content_list, embeddings_list)
        topics_over_time = self.__calculate_topics(content_list, created_at_list)
        total_topics = len(self.model.get_topics())-1
        num_topics = min(MAX_TOPICS, total_topics)

        topic_plots = []
        topic_pie_slices = []
        topic_size = self.model.topic_sizes_
        for i in topic_size.keys():
            if 0 <= i < num_topics:
                topic_pie_slices.append(
                    PieSlice(
                        name=f"topic_{i}",
                        value=topic_size[i],
                        color="grey"
                    )
                )
        topic_plots.append(
            PieChart(
                category="topics",
                slices=sorted(topic_pie_slices, key=lambda x: x.name),
            )
        )
        time_serie_data = [
            row.strftime("%d %b %H:%M") for row in topics_over_time.Timestamp.unique()
            ]
        doc_info = self.model.get_document_info(content_list)
        topic_timeline_series = []
        for topic in range(num_topics):
            topic_words = self.model.get_topic(topic) or []
            valid_words = [item for item in topic_words if isinstance(item, tuple) and len(item) == 2][:MAX_WORDS] 
                
            df_filtered = topics_over_time.loc[(topics_over_time["Topic"] == topic)].sort_values('Timestamp', ascending=False)
            
            topic_docs = doc_info[doc_info['Topic'] == topic].sort_values('Probability', ascending=False)

            try:
                name, description = self.llm_repository.create_topic_name_and_summary(num_keywords= 8, 
                                                                            num_docs= 8, 
                                                                            keywords = valid_words, 
                                                                            docs_list= topic_docs["Document"].tolist())
            except:
                name = self.model.get_topic_info(topic)["Name"].iloc[0] 
                description = f"Documento Representativo: {topic_docs['Document'].tolist()[0]}"

            topic_represetation = DocumentGroup(
                group=f"topic_{topic}",
                documents=[
                    ContentText(
                        is_representative=row["Representative_document"],
                        content=row["Document"],
                        x_coor=reduced_embeddings[id][0],
                        y_coor=reduced_embeddings[id][1]
                    ) for id, row in topic_docs.iterrows()
                ]
            )


            topic_barplot = Barplot(
                category=f"topic_{topic}",
                bars=[
                    BarPlotUnit(
                        name=word,
                        value=float(score)
                    ) for word, score in valid_words
                ]
            )
            
            topic_wordcloud = Wordcloud(
                category=f"topic_{topic}",
                data=[
                    Word(
                        name=word,
                        frequency=int(float(score)*10)
                    ) for word, score in valid_words
                ]
            )

            # topic_timeline = Timeline(
            #     messure="topics",
            #     x=[row["Timestamp"].isoformat() for _, row in df_filtered.iterrows()],
            #     y=[row["Frequency"] for _, row in df_filtered.iterrows()]
            # )

            topic_info = TopicInfo(
                topic=f"topic_{topic}",
                title=name,
                summary=description
            )

            serie_data = [0 for _ in range(len(time_serie_data))]
            for _, row in df_filtered.iterrows():
                time_index = time_serie_data.index(row["Timestamp"].strftime("%d %b %H:%M"))
                serie_data[time_index] += row["Frequency"]
            topic_timeline_series.append(
                StackedSerie(
                    name=f"topic_{topic}",
                    data=serie_data
                )
            )
            # topic_plots.append(topic_timeline)
            topic_plots.append(topic_barplot)
            topic_plots.append(topic_wordcloud)
            topic_plots.append(topic_represetation)
            topic_plots.append(topic_info)

        topic_stackline = StackedLine(
            title="topics",
            x=time_serie_data,
            series=topic_timeline_series
        )
        topic_plots.append(topic_stackline)

        return self.__parse_response(topic_plots)

    @staticmethod
    def __parse_response(response):
        parsed_response = defaultdict(dict)
        for chart in response:
            # print(type(chart))
            parsed_response[type(chart).__name__].update(chart.model_dump())
        # print((parsed_response))
        return dict(parsed_response)
