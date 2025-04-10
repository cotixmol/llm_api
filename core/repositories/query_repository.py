import typing


class Query:

    def __init__(self) -> None:
        """Inicializa el objeto Query con un body standard vacío"""
        
        self.body = {
            "track_total_hits": "true",
            "sort": [],
            "aggs": {},
            "size": 0,
            "runtime_mappings": {},
            "_source": [],
            "query": {
                "bool": {
                    "must": [],
                    "filter": [],
                    "should": [],
                    "must_not": []
                }
            }
        }

    def get_query(self) -> typing.Dict:
        return self.body
    
    # ---------------- Search configuration ----------------
    def set_date_range(self, since_iso_time: str, to_iso_time: str):
        """Establece un filtro por fechas

        Args:
            since_iso_time (str): Fecha más antigua en formato iso8601
            to_iso_time (str): Fecha más reciente en formato iso8601
        """
        for condition in  self.body["query"]["bool"]["must"]:
            if "range" in condition.keys():
                self.body["query"]["bool"]["must"].remove(condition)
                

        self.body["query"]["bool"]["must"].append(
            {
                "range": {
                    "created_at": {
                        "format": "strict_date_optional_time",
                        "gte": since_iso_time,
                        "lte": to_iso_time
                    }
                }
            }
        )
        return

    def set_pagination(self, page_size: int, page_number: int) -> None:
        self.body["size"] = page_size
        self.body["from"] = (page_number - 1) * page_size
        return

    def set_fields(self, fields: typing.List[str]) -> None:
        """Define que campos retorna elasticsearch

        Args:
            fields (typing.List[str]): Lista de campos con el nombre como figuran en kibana
        """
        self.body["_source"] = fields
        return

    def set_size(self, size: int) -> None:
        self.body["size"] = size
        return
    
    def set_sort(self, sort_field: str, sort_options: typing.Dict) -> None:
        """
        Parameters:
        - sort_field: The field to sort by.
        - sort_options: A dictionary containing the sort options (order, mode, type, etc).
        """
        self.body["sort"].append(
            {
                sort_field: sort_options
            }
        )
        return
    
    
    def set_search_after(self, search_after: typing.List[str]) -> None:
        self.body["search_after"] = search_after
        return
    
    def clean_search_after(self) -> None:
        self.body.pop("search_after")
        return
    
    def set_pit(self, id: str, keep_alive: str = "1m"):
        """
          Parameters:
          - id: pit id from open_point_in_time function
          - keep_alive: extends the time to live of the corresponding point in time.
        """
        self.body["pit"] = {
            "id": id,
            "keep_alive": keep_alive
        }
        return
    
    def clean_pit(self) -> None:
        self.body.pop("pit")
        return
    

    # ---------------- Filters configuration ----------------
    def __get_content_words_query(self, words: typing.List[str]):
        """
        Funcion privada para generar una query cobre campo content 
        teniendo en cuenta el uso de comodines
        """
        shoulds = []
        for word in words:
            if "*" in word:
                shoulds.append(
                    {
                        "bool": {
                            "should": [
                                {
                                    "query_string": {
                                        "fields": ["content"],
                                        "query": word
                                    }
                                }
                            ],
                            "minimum_should_match": 1
                        }
                    }
                )
            else:
                shoulds.append(
                    {
                        "bool": {
                            "should": [
                                {
                                    "match_phrase": {
                                        "content": word
                                    }
                                }
                            ],
                            "minimum_should_match": 1
                        }
                    }
                )
        return shoulds

    def set_filters(self, filters: typing.Dict) -> None:
        """
        Esta funcion es especifica para manager.
        Aplica los filtros seteados por el usuario en el frontend
        """
        if filters.get("category", []):
            self.body["query"]["bool"]["filter"].append(
                {
                    "bool": {
                        "minimum_should_match": 1,
                        "should": [
                            {
                                "match_phrase": {
                                    "category": category
                                }
                            } for category in filters["category"]
                        ]
                    }
                } 
            )
        if filters.get("sentiment", []):
            self.body["query"]["bool"]["filter"].append(
                {
                    "bool": {
                        "minimum_should_match": 1,
                        "should": [
                            {
                                "match_phrase": {
                                    "sentiment_name": sentiment
                                }
                            } for sentiment in filters["sentiment"]
                        ]
                    }
                } 
            )
        if filters.get("emotion", []):
            self.body["query"]["bool"]["filter"].append(
                {
                    "bool": {
                        "minimum_should_match": 1,
                        "should": [
                            {
                                "match_phrase": {
                                    "emotion": emotion
                                }
                            } for emotion in filters["emotion"]
                        ]
                    }
                } 
            )
        if filters.get("lang", []):
            self.body["query"]["bool"]["filter"].append(
                {
                    "bool": {
                        "minimum_should_match": 1,
                        "should": [
                            {
                                "match_phrase": {
                                    "lang": lang
                                }
                            } for lang in filters["lang"]
                        ]
                    }
                } 
            )
        if filters.get("words"):
            self.body["query"]["bool"]["filter"].append(
                {
                    "bool": {
                        "minimum_should_match": 1,
                        "should": self.__get_content_words_query(filters["words"])
                    }
                }
            )
        if filters.get("not_words"):
            self.body["query"]["bool"]["filter"].append(
                {
                    "bool": {
                        "must_not": {
                            "bool": {
                                "should": self.__get_content_words_query(filters["not_words"]),
                                "minimum_should_match": 1
                            }
                        }
                    }
                }
            )
        return

    def set_query_string(self, query_string: str) -> None:
        self.body["query"]["bool"]["filter"].append(
            {
                "query_string": {
                    "query": query_string
                }
            }
        )
        return

    def set_match_by_field(self, field: str) -> None:
        """Asegura que los documentos tengan el campo requerido

        Args:
            field (str): nombre del campo requerido
        """
        self.body["query"]["bool"]["filter"].append(
            {
                "bool": {
                    "should": [
                        {
                            "exists": {
                                "field": field
                            }
                        }
                    ]
                }
            }
        )
        return

    def set_not_match_by_field(self, field: str) -> None:
        """Asegura que los documentos NO tengan el campo a excluir

        Args:
            field (str): Nombre del campo a excluir
        """
        self.body["query"]["bool"]["must_not"].append(
            {
                "exists": {
                    "field": field
                }
            }
        )
        return

    def set_not_match_by_field_and_content(self, field: str, text: str) -> None:
        """Asegura que los documentos NO contengan campos con un valor

        Args:
            field (str): nombre del campo
            text (str): valor a excluir
        """
        self.body["query"]["bool"]["must_not"].append(
            {
                "match_phrase": {
                    f"{field}.keyword": text
                }
            }
        )
        return
    
    def set_match_by_field_and_content(self, field: str, text: str) -> None:
        """Asegura que los documentos NO contengan campos con un valor

        Args:
            field (str): nombre del campo
            text (str): valor a excluir
        """
        self.body["query"]["bool"]["must"].append(
            {
                "match_phrase": {
                    f"{field}.keyword": text
                }
            }
        )
        return
    
    def set_field_range_value_lt(self, field: str, lt_value: any) -> None:
        """Asegura que un campo numerico sea menor que un valor

        Args:
            field (str): nombre del campo
            lt_value (any): valor umbral
        """
        self.body["query"]["bool"]["must"].append(
            {
                "range": {
                    field: {
                        "lte": lt_value
                    }
                }
            }
        )
    
    def set_field_range_value_gt(self, field: str, gt_value: any) -> None:
        """Asegura que un campo numerico sea menor que un valor

        Args:
            field (str): nombre del campo
            lt_value (any): valor umbral
        """
        self.body["query"]["bool"]["must"].append(
            {
                "range": {
                    field: {
                        "gt": gt_value
                    }
                }
            }
        )

        
    def set_match_by_field_and_content(self, field: str, text: str) -> None:
        """Asegura que los documentos contengan campos con un valor

        Args:
            field (str): nombre del campo
            text (str): valor a excluir
        """
        self.body["query"]["bool"]["must"].append(
            {
                "match_phrase": {
                    field: text
                }
            }
        )
        return
    
    def set_terms_must_query(self, field: str, values: typing.List[str]) -> None:
        """Filtra busqueda por terms. Es una especie de filtro

        Args:
            field (str): Campo por el cual se quiere filtrar
            values (typing.List[str]): Valores que debe incluir.
        """
        self.body["query"]["bool"]["must"].append(
            {
                "terms": {
                    f"{field}.keyword": values
                }
            }
        )
        return

    # ---------------- Aggregations configuration ----------------
    def set_numerical_aggregation(self, name: str, aggregation: str, field: str) -> None:
        """Realiza un calculo sobre campo numérico.
            por ejemplo; aggregation = ["avg", "sum", "max"]
        """
        self.body["aggs"][name] = {
            aggregation: {
                "field": field
            }
        }
        return
    
    def set_numerical_aggregation_with_filter(self, name: str, aggregation: str, field: str) -> None:
        """Realiza un calculo sobre campo numérico filtrando solo documentos que contengan valor.
            por ejemplo; aggregation = ["avg", "sum", "max"]
        """
        self.body["aggs"][name] = {
            "filter": {
                    "exists": {
                    "field": field
                }
                    },
                    "aggs": {
                      name: {
                        aggregation: {
                          "field": field
                        }
                      },
                      "maximo":{
                          "max": {
                              "field": field
                          }
                      },
                      "minimo": {
                          "min": {
                              "field": field
                          }
                      }
                    }
        }
        return

    def set_time_aggregation(self, name: str, field: str, interval: str, format: str) -> None:
        self.body["aggs"][name] = {
            "date_histogram": {
                "field": field,
                "fixed_interval": interval,
                "format": format,
                "min_doc_count": 0
            }
        }
        return

    def set_time_aggregation_with_metric(self, name: str, date_field: str, date_interval: str, date_format: str, metric_type: str, metric_field: str) -> None:
        self.body["aggs"][name] = {
            "date_histogram": {
                "field": date_field,
                "fixed_interval": date_interval,
                "format": date_format,
                "min_doc_count": 0
            },
            "aggs": {
                "timeline": {
                    metric_type: {
                        "field": metric_field
                    }
                }
            }
        }
        return

    def set_terms_aggregation(self, name: str, field: str, size: int = 10) -> None:
        self.body["aggs"][name] = {
            "terms": {
                "field": f"{field}.keyword",
                "order": {"_count": "desc"},
                "size": size
            }
        }
        return
    
    def set_multiple_terms_aggregation(self, name: str, fields: list, aggs: dict, size: int = 20) -> None:
        """
        Realiza una agregación por más de un campo.
        
        Parameters:
            - name (str): Nombre del gráfico.
            - fields (list): Los campos para realizar las agregaciones. Puede ser de longitud 1 o 2.
            - aggs (dict): Agregaciones internas, en el caso de que se quiera hacer max, sum, cardinality, etc de un campo.
        
        Example:
            set_multiple_terms_aggregation("aggregation_name", ["field1", "field2"], {"sum_field": {"sum": {"field": "field_name"}}})
        """
        if len(fields) > 2:
            raise ValueError("La lista de campos debe contener 1 o 2 campos.")

        # Construir agregación para un solo campo
        def build_single_field_aggregation(field: str, aggs: dict, size: int) -> dict:
            return {
                "terms": {
                    "field": f"{field}.keyword",
                    "order": {"_count": "desc"},
                    "size": size
                },
                "aggs": aggs
            }

        # Construir agregación para dos campos
        def build_double_field_aggregation(fields: list, aggs: dict, size: int) -> dict:
            return {
                "terms": {
                    "field": f"{fields[0]}.keyword",
                    "order": {"_count": "desc"}
                },
                "aggs": {
                    "term_aggregation": build_single_field_aggregation(fields[1], aggs, size=size)
                }
            }

        # Seleccionar método de construcción de agregación basado en la cantidad de campos
        if len(fields) == 1:
            aggregation = build_single_field_aggregation(fields[0], aggs, size=size)
        else:
            aggregation = build_double_field_aggregation(fields, aggs, size=size)

        self.body["aggs"][name] = aggregation
        return


    def set_terms_aggregation_with_time_metric(self, term_name: str, term_field:str, metric_name: str, date_field: str, date_interval: str, date_format: str) -> None:
        """Realiza una agregacion y la representa en el tiempo

        Args:
            term_name (str): nombre del grafico
            term_field (str): campo por el cual agrupa
            metric_name (str): nombre de lo que se quiere medir (dejar en posts_over_time)
            date_field (str): Campo de fecha
            date_interval (str): intervalos en los cuales se cuentan documentos
            date_format (str): formato de fecha a mostrar
        """
        self.body["aggs"][term_name] = {
            "terms": {
                "field": f"{term_field}.keyword",
                "order": {
                    "_count": "desc"
                }
            },
            "aggs": {
                metric_name: {
                    "date_histogram": {
                        "field": date_field,
                        "fixed_interval": date_interval,
                        "format": date_format,
                        "min_doc_count": 0
                    }
                }
            }
        }
        return

    def set_custom_agg(self, agg: dict, name: str) -> None:
        self.body["aggs"][name] = agg
        return
    
    ##Función provisoria para poder crear knn queries sin refactorizar toda la clase query
    ##TO DO
    def set_knn_query(self, query_vector: list, k: int, num_candidates: int) -> None:
        filters = self.body.get("query", {}).get("bool", {}).get("filter", [])        
        knn_query = {
            "field": "embedding",
            "query_vector": query_vector,
            "k": k,
            "num_candidates": num_candidates
        }
        if filters:
            if len(filters) == 1:
                knn_query["filter"] = filters[0]
            else:
                knn_query["filter"] = {"bool": {"must": filters}}

        self.body = knn_query

