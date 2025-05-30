from typing import List, Dict
import pandas as pd
from V2.api.dtos.topics_dto import TopicsResponse
from V2.core.interfaces.services.topics_modelling_service_repository_interface import RawTopicAnalysis
from V2.core.interfaces.services.llm_service_repository_interface import EnrichedTopic
from V2.core.objects.pie import PieChart, PieSlice
from V2.core.objects.barplot import Barplot, BarPlotUnit
from V2.core.objects.wordcloud import Wordcloud, Word
from V2.core.objects.document import DocumentGroup, ContentText
from V2.core.objects.topic_info import TopicInfo
from V2.core.objects.stackedline import StackedLine, StackedSerie
from collections import defaultdict


def map_to_response(
    raw: RawTopicAnalysis,
    enriched: List[EnrichedTopic]
) -> TopicsResponse:
    """
    Toma el análisis crudo de tópicos (raw) y la lista de topics enriquecidos (enriched)
    y construye el DTO TopicsResponse:
      - data: lista de dicts con topic_id, name, summary
      - chart: dict con todos los charts serializados
      - n_docs: total de documentos procesados
    """
    # 1) Pie chart de tamaño de tópicos
    sizes = {
        tid: raw.doc_info[raw.doc_info["Topic"] == tid].shape[0]
        for tid in range(raw.num_topics)
    }
    slices = [
        PieSlice(name=f"topic_{tid}", value=sizes.get(tid, 0), color="grey")
        for tid in sorted(sizes)
    ]
    pie = PieChart(category="topics", slices=slices)

    # 2) Barras, nubes de palabras y grupos de documentos
    barplots = []
    wordclouds = []
    docgroups = []
    for tid in range(raw.num_topics):
        # keywords + scores
        kw_scores = raw.topics_dict.get(tid, [])
        # Barplot
        barplots.append(
            Barplot(
                category=f"topic_{tid}",
                bars=[BarPlotUnit(name=kw, value=float(score)) for kw, score in kw_scores],
            )
        )
        # Wordcloud
        wordclouds.append(
            Wordcloud(
                category=f"topic_{tid}",
                data=[Word(name=kw, frequency=int(score * 10)) for kw, score in kw_scores]
            )
        )
#############REVISAAAAAAAAAAAAAAAR
        # DocumentGroup con coordenadas y texto
        docs_df = raw.doc_info[raw.doc_info["Topic"] == tid].sort_values(
            "Probability", ascending=False
        )
        documents = []
        for idx, row in docs_df.iterrows():
            x, y = raw.reduced_embeddings[idx]
            is_rep = (row.name == docs_df.index[0])
            documents.append(
                ContentText(
                    is_representative=is_rep,
                    content=row["Document"],
                    x_coor=x,
                    y_coor=y,
                )
            )
        docgroups.append(DocumentGroup(group=f"topic_{tid}", documents=documents))

    # 3) TopicInfo usando enriched
    info_objs = [
        TopicInfo(
            topic=f"topic_{et.topic_id}",
            title=et.name,
            summary=et.summary,
        )
        for et in enriched
    ]

    # 4) Stacked line (evolución temporal)
    timestamps = [ts.isoformat() for ts in raw.topics_over_time.Timestamp.unique()]
    series = []
    for tid in range(raw.num_topics):
        freq = (
            raw.topics_over_time[
                raw.topics_over_time["Topic"] == tid
            ].set_index("Timestamp")["Frequency"]
        )
        data = [int(freq.get(pd.to_datetime(t), 0)) for t in timestamps]
        series.append(StackedSerie(name=f"topic_{tid}", data=data))
    stacked = StackedLine(title="topics", x=timestamps, series=series)

    # 5) Fusionar todos los charts en un dict serializable
    charts = [pie] + barplots + wordclouds + docgroups + info_objs + [stacked]
    # chart_dict: Dict[str, dict] = {}
    # for chart in charts:
    #     chart_dict.update({type(chart).__name__: chart.model_dump()})
    parsed_response = defaultdict(dict)
    for chart in charts:
        # cada chart.model_dump() devuelve un dict con **una sola clave**
        # que identifica la categoría dentro del tipo de gráfico
        parsed_response[type(chart).__name__].update(chart.model_dump())

    chart_dict = dict(parsed_response)


    # 6) Data: lista básica de topics enriquecidos
    data = [
        {"topic_id": et.topic_id, "name": et.name, "summary": et.summary}
        for et in enriched
    ]

    return TopicsResponse(data=data, chart=chart_dict, n_docs=raw.doc_info.shape[0])