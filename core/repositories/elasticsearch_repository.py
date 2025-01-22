from core.objects.index import Index
from core.objects.document import Document
from core.objects.wordcloud import Wordcloud, Word
from core.objects import table_author
from core.objects import table_source
from core.objects import table_interaction
from core.objects.radar import Radar, RadarUnit
from core.objects.timeline import Timeline
from core.objects.heatmap import HeatMap, Point
from core.objects.lineal_heatmap import LinealHeatmap
from core.objects.histogram_point import HistogramPoint, Histogram
from core.objects.pie import PieChart, PieSlice, ColorPalet
from core.objects.barplot import Barplot, BarPlotUnit
from core.objects.network_graph import NetworkGraph, NetworkCategory, NetworkLink, NetworkNode
from core.objects.trending_chart import Trend, TrendChart
from core.objects.metric import Metric
from services.elasticsearch_service import ElasticsearchService
from repositories.query_repository import Query
from api.config.logger import logger
import typing
import pandas as pd
import numpy as np
from itertools import permutations
from collections import defaultdict

class ElasticsearchRepository:

    def __init__(self, elasticsearch_service: ElasticsearchService, page_size: int = 1000):
        self.elasticsearch_service = elasticsearch_service
        self.page_size = int(page_size)

    ### SEARCH METHODS ###

    async def get_workspace_indexes(self,
                                    workspace: str) -> typing.List[Index]:
        workspace_indexes = await self.elasticsearch_service.get_indexes_information(
            index_patern=f"in-{workspace}-*")
        return [
            Index(index=index.index,
                  n_docs=index.docs_count,
                  size_bytes=index.pri_store_size)
            for index in workspace_indexes
        ]

    async def get_aggs_data(self, index_pattern: str, body: typing.Dict) -> typing.Dict:
        response = await self.elasticsearch_service.run_search_query(
            index_pattern=index_pattern,
            query=body
        )
        aggs_data = defaultdict(dict)
        for agg_name, agg_result in response.aggregations.items():
            aggs_data[agg_name] = {
                item["key"].lower(): aggs_data[agg_name].get(item["key"].lower(), 0) + item["doc_count"]
                for item in agg_result["buckets"] if item["key"]
            }
        return dict(aggs_data)
    
    async def get_index_data(self, index_pattern: str, body: dict ) -> typing.Tuple[typing.List[Document], typing.List]:
        search_results = await self.elasticsearch_service.run_search_query(
            index_pattern=index_pattern, query=body)
        if not search_results.hits:
            return ([], [])
        documents = [
            Document(
                **doc
            )
            for doc in search_results.hits
        ]
        return documents, search_results.last_sort_id
    
    async def search_data(self, index_pattern: str, query: Query, max_ndocs: int = 0) -> typing.List[Document]:
        total_hits = []
            
        standar_index = self.elasticsearch_service.standard_index(index=index_pattern)
        query.set_size(self.page_size)
        package_size = self.page_size
        last_sort = []
        i = 1
        while package_size == self.page_size:

            if _N_DOCS >= max_ndocs and max_ndocs != 0:
                break

            if last_sort:
                query.set_search_after(last_sort)

            es_response = self.elasticsearch_service.run_search_query(
                index_pattern=standar_index, 
                query=query.body
            )

            hits = es_response.hits
            package_size = len(hits)
            logger.debug(f"{package_size} documents brought in the page number {i} from the index: {standar_index}") 
            i+=1
            if not hits:
                logger.info(f"No documents found for index {standar_index}")
                break
            
            last_sort = hits[-1]["sort"]
            total_hits.extend(hits)
            _N_DOCS = len(total_hits) 
        documents = [
            Document(
                **doc
            )
            for doc in total_hits
        ]
        return documents

    ### CHART METHODS ###

    async def get_index_data_preview_and_histogram(
            self,
            index_pattern: str,
            body: dict
    ) -> typing.Tuple[typing.List[Document], Histogram, int]:
        search_results = await self.elasticsearch_service.run_search_query(
            index_pattern=index_pattern, query=body)
        documents = [
            Document(
                **doc
            )
            for doc in search_results.hits
        ]
        histogram_points=[]
        if search_results.aggregations:
            histogram_points = [
                HistogramPoint(
                    key=point["key_as_string"], 
                    value=point["doc_count"])
                for point in search_results.aggregations['histogram_data']['buckets']
            ]
        histogram = Histogram(points=histogram_points)
        n_docs = len(documents)
        if search_results.aggregations:
            for point in search_results.aggregations['histogram_data']['buckets']:
                n_docs += point["doc_count"]
        return documents, histogram, search_results.total_hits

    async def get_histogram(self, name:str, bucket: list) -> Histogram:
        histogram_points=[]
        for bucket in bucket["buckets"]:
            histogram_points.append(
                HistogramPoint(
                    key=bucket["key_as_string"], 
                    value=bucket["doc_count"]
                )
            )
        return Histogram(points=histogram_points)
        
    async def get_metric_timeline_chart(
            self,
            bucket: dict,
            name:str
            ) -> Timeline:
        x_points = []
        y_points = []
        for point in bucket["buckets"]:
            x_points.append(point["key_as_string"])
            y_points.append(point["timeline"]["value"])
        return Timeline(messure=name, x=x_points, y=y_points)

    async def get_heatmap_chart(
            self,
            data: typing.List[typing.Dict]
    ) -> HeatMap:
        points = []
        for hit in data:
            if hit.get("coordinates"):
                points.append(
                    Point(
                        lat=hit["coordinates"][1],
                        lon=hit["coordinates"][0]
                    )
                )        

        return HeatMap(coordinates=points)

    async def get_pie_chart(
            self,
            name: str,
            bucket: dict
    ) -> PieChart:
        pie_slices = []
        for slice in bucket["buckets"]:
            key = slice["key"]
            value = slice["doc_count"]
            color_key = key.split()[0]
            sentiment_map = {
                "NEU": "neutral",
                "POS": "positive",
                "NEG": "negative"
            }
            if (color_key in sentiment_map.keys()):
                color_key = sentiment_map[color_key]
            color = ColorPalet[color_key] if color_key in ColorPalet.__members__ else ColorPalet["others"]
            pie_slices.append(PieSlice(name=key, value=value, color=color.value))
        return PieChart(category=name, slices=pie_slices)

    async def get_barplot(self, name: str, bucket: dict):
        barplot = []
        keySet = set()
        
        for bucket_item in bucket["buckets"]:
            key = bucket_item["key"]
            value = bucket_item["sum_interactions"]["value"] if name == "authors_by_interactions" else bucket_item["doc_count"]
            key_lower = key.lower()
            if key_lower not in keySet and value > 0:
                if name == "geoname":
                    if key != key.upper():
                        barplot.append(BarPlotUnit(name=key.capitalize(), value=value))
                else:
                    barplot.append(BarPlotUnit(name=key.capitalize(), value=value))
                    keySet.add(key_lower)
            else:
                for bar in barplot:
                    if bar.name.lower() == key_lower:
                        bar.value += value
        
        barplot = sorted(barplot, key=lambda x: x.value, reverse=True)
        return Barplot(category=name, bars=barplot)

    async def get_radar(self, name: str, bucket: dict):
        radar = []
        for bucket in bucket["buckets"]:
            key = bucket["key"]
            value = bucket["doc_count"]
            radar.append(RadarUnit(name=key, value=value))
        return Radar(category=name, radars=radar)
    
    async def get_table_authors(self, name: str, bucket: dict):
        table = []
        for buck in bucket.get("buckets", []):
            key = buck.get("key", "")
            documents = buck.get("doc_count", 0)
            term_aggregation_buckets = buck.get("term_aggregation", {}).get("buckets", [])
            
            category = term_aggregation_buckets[0].get("key", "") if term_aggregation_buckets else ""
            followers = term_aggregation_buckets[0].get("max_follower", {}).get("value", 0) if term_aggregation_buckets else 0
            reach = term_aggregation_buckets[0].get("sum_reach", {}).get("value", 0) if term_aggregation_buckets else 0
            engagement = term_aggregation_buckets[0].get("max_egagement", {}).get("value", 0) if term_aggregation_buckets else 0
            
            table.append(table_author.RowAuthor(name=key, value=documents, category=category, followers=followers, reach=reach, engagement=engagement))
        
        return table_author.Table(category=name, table=table)
    
    async def get_table_sources(self, name: str, bucket: dict):
        table = []
        for buck in bucket["buckets"]:
            source = buck.get("key", "")
            documents = buck.get("doc_count", 0)
            total_reach = buck["sum_reach"]["value"]
            unique_authors = buck["cardinality_author"]["value"]
            avg_engagement = buck["avg_engagement"]["value"]
            table.append(table_source.RowSource(source=source, documents=documents, total_reach=total_reach, unique_authors=unique_authors, avg_engagement=avg_engagement))
        return table_source.Table(category=name, table=table)
    
    async def get_table_interactions(self, data: dict):
        table = []
        dataOrdered = sorted(data, key=lambda x: -x.get("interactions", 0))
        content_set = set()
        for row in dataOrdered:
            content = row.get("content", "")
            if content not in content_set:
                table.append(
                    table_interaction.Row(
                        source=row.get("source", ""),
                        author=row.get("author", ""),
                        content=content if content else "",
                        interactions=row.get("interactions", 0),
                        category=row.get("category", "")
                    )
                )
                content_set.add(content)
                if len(table) == 20:
                    break
        return table_interaction.Table(category="interactions", table=table)

    async def get_wordcloud(self, name: str, bucket: dict):
        def soft_max_scaler(values: pd.Series, max_value: int = 1):
            if all(i == values[0] for i in values):     # This is a WA for border cases where values are all equals
                return values
            return max_value / (1 + np.exp(-(values - values.mean()) / values.std())).fillna(0)

        if not bucket["buckets"]:
            return Wordcloud(category=name, data=[])

        df = pd.DataFrame(bucket["buckets"])
        df["doc_count"] = soft_max_scaler(df["doc_count"], 60)
        df = df.fillna("")

        tokens = [{"text": buck["key"], "frequency": buck["doc_count"]} for buck in df.to_dict("records")]
        tokens_df = pd.DataFrame(tokens)

        tokens_df["frequency"] = soft_max_scaler(tokens_df["frequency"], 60)

        wordcloud = [Word(name=row["text"], frequency=row["frequency"]) for _, row in tokens_df.iterrows()]

        return Wordcloud(category=name, data=wordcloud)

    async def get_lineal_heatmap(self, name: str, bucket: dict) -> LinealHeatmap:
        yAxis = []
        xAxis = []
        data = []
        for bucket_item in bucket["buckets"]:
            term_item = bucket_item["key"]
            yAxis.append(term_item)
            for point in bucket_item["posts_over_time"]["buckets"]:
                key = point["key_as_string"]
                if key not in xAxis:
                    xAxis.append(key)
                data.append(
                    [
                        yAxis.index(term_item),
                        xAxis.index(key),
                        point["doc_count"]
                    ]
                )
        return LinealHeatmap(title=name, yAxis=yAxis, xAxis=xAxis, data=data)

    async def get_network_graph(self, name, data) -> NetworkGraph:
        def softmax_size(values: list, max_value: int = 1) -> list:
            if not values:
                return 0.0
            return float(max_value/np.max(values))
        combinations = []
        nodes = []
        links = []
        # TODO: move categories to custom method logic
        categories = [
            NetworkCategory(
                name="Positive"
            ),
            NetworkCategory(
                name="Negative"
            ),
            NetworkCategory(
                name="Neutral"
            )
        ]
        for node in data["buckets"]:
            nodes.append(
                NetworkNode(
                    name=node["key"],
                    value=int(node["doc_count"]),
                    category=0 if int(node["sent"]["value"]) > 0 else 1  # TODO: how to get this shit?
                )
            )
            for link in node["co_occur"]["buckets"]:
                if (
                    (node["key"], link["key"]) in combinations 
                    or link["key"] not in [node.name for node in nodes] 
                    or link["key"] == node["key"]
                ):
                    continue
                combinations.extend(
                    permutations([node["key"], link["key"]], 2)
                )
                links.append(
                    NetworkLink(
                        source=node["key"],
                        target=link["key"],
                        value=link["doc_count"]
                    )
                )
        # Elimina los nodos que no se vinculan
        nodes = [node for node in nodes if any([node.name in comb for comb in combinations])]
        soft_scalar = softmax_size(values=[node.value for node in nodes], max_value=50)
        for node in nodes:
            node.soft_size = round(node.value*soft_scalar, 2)
            # node.soft_size = float(np.exp(node.value))*soft_scalar
        return NetworkGraph(
            title=name,
            nodes=nodes,
            links=links,
            categories=categories
        )
    
    async def get_metric_chart(self, name: str, data: dict) -> Metric:
        total = data["doc_count"]
        if not total:
            return Metric(
                name=name,
                value=0,
                total=total,
                max=0,
                min=0
            )
        # print(name, data)
        value = 0
        maximo = data["maximo"]["value"]
        minimo = data["minimo"]["value"]
        for k, v in data.items():
            if name in k:
                value = v.get("value", 0)
        return Metric(
            name=name,
            value=round(value, 2),
            total=total,
            max=round(maximo, 2),
            min=round(minimo, 2)
        )

    async def get_query_charts(self, index_pattern: str, body: typing.Dict) -> typing.List:
        response = await self.elasticsearch_service.run_search_query(
            index_pattern=index_pattern,
            query=body
        )
        library = []
        for name, data in response.aggregations.items():
            if "histogram" in name:
                library.append(await self.get_histogram(
                                                name=name.replace("histogram_", ""),
                                                bucket=data
                                            )
                )
            elif "timeline" in name:
                library.append(await self.get_metric_timeline_chart(
                                                name=name.replace("timeline_", ""),
                                                bucket=data
                                            )
                )
            elif "piechart" in name:
                library.append(await self.get_pie_chart(
                                                name=name.replace("piechart_", ""),
                                                bucket=data
                                            )
                )
            elif "barplot" in name:
                library.append(await self.get_barplot(
                                                name=name.replace("barplot_", ""),
                                                bucket=data
                                            )
                )
            elif "radar" in name:
                library.append(await self.get_radar(
                                                name=name.replace("radar_", ""),
                                                bucket=data
                                            )
                )
            elif "table_authors" in name:
                library.append(await self.get_table_authors(
                                                name=name.replace("table_", ""),
                                                bucket=data
                                            )
                )
            elif "table_sources" in name:
                library.append(await self.get_table_sources(
                                                name=name.replace("table_", ""),
                                                bucket=data
                                            )
                )
            elif "wordcloud" in name:
                library.append(await self.get_wordcloud(
                                                name=name.replace("wordcloud_", ""),
                                                bucket=data
                                            )
                )
            elif "lineal_heatmap" in name:
                library.append(await self.get_lineal_heatmap(
                    name=name.replace("lineal_heatmap_", ""),
                    bucket=data
                ))
            elif "network_graph" in name:
                library.append(
                    await self.get_network_graph(
                        name=name.replace("network_graph_", ""),
                        data=data
                    )
                )
            elif "average" in name:
               library.append(
                   await self.get_metric_chart(
                    name=name.replace("_average", ""),
                    data=data
                    )
               )
        
        if response.hits and "coordinates" in body["_source"]:       
            library.append(await self.get_heatmap_chart(data=response.hits))
        elif response.hits and "interactions" in body["_source"]:
            library.append(await self.get_table_interactions(data=response.hits))
        return library

    async def get_trending_charts(
            self,
            current_dataset: typing.Dict,
            previus_dataset: typing.Dict
    ) -> typing.Dict:
        library = []
        titles = list(current_dataset)
        
        for title in titles:
            if not current_dataset[title]:
                library.append(
                TrendChart(
                    title=title,
                    trends=[]
                    )
                )
                continue
            trends = []
            max_current_count = max(current_dataset[title].values())
            for trend, current_count in current_dataset[title].items():
                previus_count = previus_dataset[title].get(trend, 0)
                if previus_count:
                    evolution = round(((current_count-previus_count)/previus_count)*100, 2)
                else:
                    evolution =round((current_count/max_current_count)*100, 2)
                trends.append(
                    Trend(
                        label=trend,
                        value=current_count,
                        evolution=evolution,
                        previus=previus_count
                    )
                )
            library.append(
                TrendChart(
                    title=title,
                    trends=trends
                )
            )
        return library

