import typing
import json
import logging
from services.llm_vllm_service import LLMService
from core.objects.document import Document
from typing import List, Dict
from V2.utils.logger import logger
import json
import re
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class LLMRepository:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    @staticmethod
    def _parse_model_response(
        response_text: str, valid_labels: typing.Optional[List[str]] = None
    ) -> typing.Optional[dict]:
        """
        checks if the response_text is a valid json and if the value of the key 'task_key' is in the valid_labels
        """
        try:
            start_index = response_text.find("{")
            end_index = response_text.rfind("}") + 1
            json_text = response_text[start_index:end_index]
            response_data = json.loads(json_text)

            # Validar que el valor de la clave 'task_key' esté en las etiquetas válidas
            if valid_labels:
                for key, value in response_data.items():
                    if value not in valid_labels:
                        logging.warning(
                            f"Etiqueta no válida '{value}' para la clave '{key}'."
                        )
                        return None
            return response_data
        except (ValueError, json.JSONDecodeError):
            logging.warning(
                f"Formato incorrecto en la respuesta del modelo. Response: {response_text}"
            )
            return None

    def _parse_summary_response(self, response_text: str) -> typing.Optional[dict]:
        """
        Intenta extraer y parsear el bloque JSON esperado de la respuesta utilizando tres enfoques.
        Se espera un formato: { "category": "...", "summary": [...] }

        En primer lugar, se usa el método original (buscar el primer '{' y el último '}').
        Si falla, se utiliza un enfoque robusto que limpia delimitadores Markdown y usa regex.
        Si aún falla, se aplica un tercer enfoque que intenta corregir comillas simples inconsistentes.
        """
        # Primer intento: método original
        try:
            start_index = response_text.find("{")
            end_index = response_text.rfind("}") + 1
            json_text = response_text[start_index:end_index]
            response_data = json.loads(json_text)
            if "category" in response_data and "summary" in response_data:
                return {response_data["category"]: response_data["summary"]}
            else:
                logging.warning(
                    f"El JSON parseado no tiene el formato esperado. Claves encontradas: {list(response_data.keys())}. Response: {json_text}"
                )
        except (ValueError, json.JSONDecodeError) as e:
            logging.warning(
                f"Fallo en el método original de parseo: {e}. Response: {response_text}"
            )

        # Segundo intento: enfoque robusto
        # Eliminar delimitadores de código (por ejemplo, ```json y ```)
        cleaned_text = re.sub(
            r"```(?:json)?", "", response_text, flags=re.IGNORECASE
        ).strip()
        cleaned_text = cleaned_text.strip("`").strip()

        # Buscar un bloque JSON usando regex que capture todo el contenido entre llaves
        match = re.search(r"({.*})", cleaned_text, re.DOTALL)
        if not match:
            logging.warning(
                f"No se encontró un bloque JSON en la respuesta del modelo. Response: {response_text}"
            )
            return None

        json_text = match.group(1)
        try:
            response_data = json.loads(json_text)
            if "category" in response_data and "summary" in response_data:
                return {response_data["category"]: response_data["summary"]}
            else:
                logging.warning(
                    f"El JSON obtenido no tiene el formato esperado. Claves encontradas: {list(response_data.keys())}. Response: {json_text}"
                )
                # Continuamos con el tercer intento
        except (ValueError, json.JSONDecodeError) as e:
            logging.warning(
                f"Fallo al parsear JSON en el segundo intento: {e}. Intentando limpieza adicional. Texto: {json_text}"
            )
            # Fallback adicional: eliminar posibles comas sobrantes
            json_text_clean = re.sub(r",\s*}", "}", json_text)
            try:
                response_data = json.loads(json_text_clean)
                if "category" in response_data and "summary" in response_data:
                    return {response_data["category"]: response_data["summary"]}
                else:
                    logging.warning(
                        f"El JSON limpiado no tiene el formato esperado. Claves encontradas: {list(response_data.keys())}. Response: {json_text_clean}"
                    )
            except (ValueError, json.JSONDecodeError) as e2:
                logging.warning(
                    f"Fallo final en el segundo intento tras limpieza adicional: {e2}. Response: {json_text_clean}"
                )
                # Continuamos con el tercer intento

        # Tercer intento: tratamiento de comillas simples
        # Se intenta reemplazar de forma cuidadosa las comillas simples por dobles en el JSON extraído.
        # Esta transformación se aplica solo en el bloque obtenido tras la limpieza adicional.
        json_text_for_quotes = (
            json_text if "json_text_clean" not in locals() else json_text_clean
        )
        # Usamos una regex para reemplazar comillas simples que rodean claves o valores, asumiendo que no forman parte del contenido interno.
        json_text_quotes = re.sub(
            r"(?<=[:{,])\s*'([^']+?)'\s*(?=[,}])", r' "\1" ', json_text_for_quotes
        )
        try:
            response_data = json.loads(json_text_quotes)
            if "category" in response_data and "summary" in response_data:
                return {response_data["category"]: response_data["summary"]}
            else:
                logging.warning(
                    f"El JSON obtenido tras corrección de comillas no tiene el formato esperado. Claves encontradas: {list(response_data.keys())}. Response: {json_text_quotes}"
                )
                return None
        except (ValueError, json.JSONDecodeError) as e3:
            logging.warning(
                f"Fallo final al parsear JSON tras corrección de comillas: {e3}. Response: {json_text_quotes}"
            )
            return None

    async def create_topics_name_and_summary(
        self,
        inference_data: typing.Dict[int, dict],
        num_keywords: int = 8,
        num_docs: int = 8,
    ) -> typing.Dict[int, dict]:
        results = {}
        pending_topics = list(inference_data.keys())
        attempt = 0
        MAX_ATTEMPTS = 6
        index = 0
        while pending_topics and attempt < MAX_ATTEMPTS:
            prompts = []
            topics_batch = []
            for topic, data in inference_data.items():
                if topic not in pending_topics:
                    continue
                if attempt < 3:
                    docs_to_use = data["docs"][: min(num_docs, len(data["docs"]))]
                    keywords_to_use = data["keywords"][
                        : min(num_keywords, len(data["keywords"]))
                    ]
                else:
                    index += 3
                    docs_to_use = data["docs"][
                        index : min(index + num_docs, len(data["docs"]))
                    ]
                    keywords_to_use = data["keywords"][
                        index : min(index + num_keywords, len(data["keywords"]))
                    ]
                try:
                    prompt = [
                        {
                            "role": "system",
                            "content": "You are an AI assistant specialized in summarizing large amounts of social media posts.",
                        },
                        {
                            "role": "user",
                            "content": f"""There is a topic composed of the following keywords: {keywords_to_use}
                                        The following documents represent a small but representative subset of all the documents belonging to the topic:
                                        {docs_to_use}

                                        Based on the above information, generate a short name or label for the topic and a brief description (maximum 3 sentences). You must respond in JSON format, following this structure:
                                        {{
                                            "topic_name": "<name>",
                                            "topic_description": "<description>"
                                        }}
                                        You MUST answer in spanish.
                                        """,
                        },
                    ]
                    prompts.append(prompt)
                    topics_batch.append(topic)

                except Exception as e:
                    logging.error(
                        f"Error al generar el prompt para el tópico '{topic}': {e}"
                    )
                    continue

            response = await self.llm_service.generate_text(
                prompts, max_new_tokens=5000
            )
            logger.info(f"response: {response}")
            # Validar la respuesta del modelo antes de guardarla
            for topic, text in zip(topics_batch, response):
                topic_summary = text
                if isinstance(topic_summary, str):
                    try:
                        response_data = self._parse_model_response(topic_summary)
                        if (
                            response_data
                            and "topic_name" in response_data
                            and "topic_description" in response_data
                        ):
                            results[topic] = {
                                "name": response_data["topic_name"],
                                "description": response_data["topic_description"],
                            }
                        else:
                            logging.warning(
                                f"Tópico {topic}: JSON sin las claves esperadas."
                            )
                    except Exception as e:
                        logging.warning(
                            f"Tópico {topic}: fallo al parsear la respuesta en el intento {attempt + 1}. Error: {e}"
                        )
                else:
                    logging.warning(
                        f"Tópico {topic}: respuesta del modelo en formato inesperado en el intento {attempt + 1}."
                    )

            # Actualizamos los tópicos pendientes
            pending_topics = [t for t in pending_topics if t not in results]
            attempt += 1

        # Informamos los tópicos a los que no se les pudo generar el informe
        for topic in pending_topics:
            logging.warning(
                f"El tópico '{topic}' no obtuvo un resumen válido tras {MAX_ATTEMPTS} intentos."
            )
        return results

        for attempt in range(MAX_ATTEMPTS):
            if attempt < 3:
                docs_to_use = docs_list[: min(num_docs, len(docs_list))]
                keywords_to_use = keywords[: min(num_keywords, len(keywords))]
            else:
                index += 3
                docs_to_use = docs_list[index : min(index + num_docs, len(docs_list))]
                keywords_to_use = keywords[
                    index : min(index + num_keywords, len(keywords))
                ]

            prompt = f"""
                        There is a topic composed of the following keywords: {keywords_to_use}
                        The following documents represent a small but representative subset of all the documents belonging to the topic:
                        {docs_to_use}

                        Based on the above information, generate a short name or label for the topic and a brief description (maximum 3 sentences). You must respond in JSON format, following this structure:
                        {{
                            "topic_name": "<name>",
                            "topic_description": "<description>"
                        }}
                        You MUST answer in spanish.
                        """
            messages = [
                {"role": "user", "content": prompt},
            ]

            try:
                outputs = await self.llm_service.generate_text(
                    messages, max_new_tokens=350
                )
                response_data = self._parse_model_response(
                    outputs[-1]["generated_text"]
                )

                try:
                    topic_name = response_data["topic_name"]
                    topic_description = response_data["topic_description"]
                    return topic_name, topic_description
                except:
                    logging.warning(
                        f"Formato incorrecto en la respuesta del modelo, intento número {attempt + 1}. Response: {response_data}"
                    )

            except Exception as e:
                logging.warning(
                    f"Error en la generación de Nombre y Tópico, intento número {attempt + 1}. Error: {e}"
                )

        logging.error(
            f"No se pudo generar una respuesta válida después de {MAX_ATTEMPTS} intentos"
        )
        return None, None

    async def apply_prompt_classification(
        self,
        prompt_template: typing.Dict[str, str],
        task_key: str,
        update_field: str,
        valid_labels: typing.List[str],
        batch_size: int,
        docs: List[dict] = None,
    ) -> typing.List[typing.Dict[str, typing.Optional[str]]]:
        if not docs:
            logging.error("docs_list no puede ser None o vacío.")
            raise ValueError("No se encontraron documentos.")
        if not prompt_template:
            logging.error("El template de prompt no puede ser None o vacío.")
            raise ValueError("No se encontró un template de prompt válido.")

        es_index_list = []
        doc_id_list = []
        content = []
        skiped_es_index_list = []
        skiped_doc_id_list = []
        skiped_category = []

        for doc in docs:
            # check if content exits in "_source" dict
            doc_content = doc.content if doc.content else "empty"
            # check if content is None, an empty string, or the word "empty"
            if not doc_content or doc_content == "empty":
                skiped_es_index_list.append(doc.index)
                skiped_doc_id_list.append(doc.id)
                skiped_category.append({task_key: None})
                continue
            content.append(doc_content)
            es_index_list.append(doc.index)
            doc_id_list.append(doc.id)

        # create a list of indices to process
        pending_indices = list(range(len(content)))
        predictions = [None] * len(content)

        # check if content is None, an empty string, or the word "empty"
        if not content:
            raise ValueError("No se encontraron documentos válidos para procesar.")

        for attempt in range(3):
            if not pending_indices:
                break

            logging.info(
                f"Intento {attempt + 1} con {len(pending_indices)} documentos pendientes."
            )

            # iteramos sobre batches de documentos de tamaño batch_size
            for i in range(0, len(pending_indices), batch_size):
                print(
                    f"Procesando batch {i // batch_size + 1} de {len(pending_indices) // batch_size + 1}"
                )
                batch_indices = pending_indices[i : i + batch_size]
                batch_prompts = [
                    [
                        {
                            "role": "system",
                            "content": prompt_template["system"],
                        },
                        {
                            "role": "user",
                            "content": prompt_template["user"].format(doc=content[idx]),
                        },
                    ]
                    for idx in batch_indices
                ]

                try:
                    output = await self.llm_service.generate_text(
                        batch_prompts, max_new_tokens=40
                    )
                    responses = output
                except Exception as batch_error:
                    logging.error(
                        f"Error procesando el batch {i // batch_size + 1}: {batch_error}"
                    )

                for idx, response in zip(batch_indices, responses):
                    try:
                        generated_text = response

                        # Parsear el texto generado
                        response_data = self._parse_model_response(
                            generated_text, valid_labels
                        )

                        # Validar si el response_data es un diccionario y contiene la clave esperada
                        if not isinstance(response_data, dict):
                            logging.warning(
                                f"Formato inesperado del response_data para el documento {idx}. Response: {response_data}"
                            )
                            continue

                        if task_key not in response_data:
                            logging.warning(
                                f"El response_data no contiene la clave '{task_key}' para el documento {idx}. Response: {response_data}"
                            )
                            continue

                        # Extraer la etiqueta y asignarla a las predicciones
                        label = response_data[task_key]
                        predictions[idx] = label
                        logging.info(
                            f"Predicción exitosa para el documento {idx}: {label}"
                        )

                    except Exception as parse_error:
                        logging.error(
                            f"Error al procesar el documento {idx}. Detalles: {parse_error}",
                            exc_info=True,
                        )

            pending_indices = [idx for idx in pending_indices if not predictions[idx]]

        for idx in pending_indices:
            logging.error(f"Documento descartado tras 5 intentos: {content[idx]}")

        category_list = [{update_field: prediction} for prediction in predictions]

        return {
            "es_index_list": es_index_list + skiped_es_index_list,
            "doc_id_list": doc_id_list + skiped_doc_id_list,
            "classification_list": category_list + skiped_category,
        }

    async def apply_prompt(self, prompt: list) -> str:
        attempts = 0
        prompt_message = [{"role": "user", "content": prompt}]
        while attempts < 5:
            try:
                output = await self.llm_service.generate_text(
                    [prompt_message], temperature=0, top_p=1, max_new_tokens=10
                )
                return output[0]
            except Exception as e:
                logging.error(
                    f"Error generando texto en el intento {attempts + 1}: {e}"
                )
                attempts += 1

        logging.error("Fallo en todos los intentos para generar texto.")
        return None

    async def apply_prompt_categories_summary(
        self, aggs: dict, prompt_template: dict, summary_field: str, batch_size: int
    ) -> Dict[str, str]:
        buckets = aggs.get("top_categories_hits", {}).get("buckets", [])
        if not buckets:
            logging.error("No se encontraron buckets en la respuesta de Elasticsearch.")
            return {}

        # Para cada bucket se extraen los contenidos de los documentos (hits) de la subagregación 'top_interactions'
        category_docs = {}
        for bucket in buckets:
            # La categoría se obtiene directamente de la clave del bucket
            category = bucket.get("key")

            # Extraer los documentos del subbucket 'top_interactions'
            hits = bucket.get("top_docs", {}).get("hits", {}).get("hits", [])

            contents = []
            for hit in hits:
                source = hit.get("_source", {})
                # Se extrae y limpia el contenido
                content = source.get("content", "").strip()
                if not content:
                    logging.warning(
                        f"Documento sin contenido en bucket '{category}': {hit}"
                    )
                    continue
                contents.append(content)

            if contents:
                # Limitar a 50 documentos por categoría
                category_docs[category] = contents[:50]
            else:
                logging.warning(
                    f"No se encontraron contenidos válidos para la categoría '{category}'."
                )

        pending_categories = list(category_docs.keys())
        summaries = {}
        MAX_ATTEMPTS = 5
        attempt = 0
        while pending_categories and attempt < MAX_ATTEMPTS:
            prompts = []
            for category, contents in category_docs.items():
                if category not in pending_categories:
                    continue
                try:
                    prompt = [
                        {
                            "role": "system",
                            "content": prompt_template["system"],
                        },
                        {
                            "role": "user",
                            "content": prompt_template["user"].format(
                                contents=contents,
                                category=category,
                                summary_field=summary_field,
                            ),
                        },
                    ]
                    prompts.append(prompt)
                except Exception as e:
                    logging.error(f"Error al generar el prompt para '{category}': {e}")
                    continue
            output = await self.llm_service.generate_text(prompts, max_new_tokens=5000)
            logger.debug(f"response: {output}")
            # Validar la respuesta del modelo antes de guardarla
            for text in output:
                if isinstance(text, str):
                    print(text)
                    category_result = self._parse_summary_response(text)
                    print(category_result)
                    if not category_result:
                        continue
                    for key, value in category_result.items():
                        summaries[key] = value
                        try:
                            pending_categories.remove(key)
                        except ValueError:
                            logging.warning(
                                f"La categoría '{key}' nunca estuvo pendiente."
                            )
            attempt += 1
        # Validamos que no existan resúmenes para categorías inventadas
        for key in list(summaries.keys()):
            if key.lower() not in [cat.lower() for cat in category_docs.keys()]:
                summaries.pop(key)
                logging.warning(
                    f"La categoría '{key}' se removió porque no es una categoría válida."
                )

        # Informamos las categorías a las que no se les pudo generar el informe
        for category in category_docs.keys():
            if category.lower() not in [key.lower() for key in summaries.keys()]:
                logging.warning(
                    f"La categoría '{category}' no obtuvo un resumen válido tras {MAX_ATTEMPTS} intentos."
                )

        return summaries

    async def apply_prompt_query_summary(
        self, docs: List[dict], prompt_template: dict, query: str
    ) -> Dict[str, str]:
        if not docs:
            logging.error("La lista de documentos no puede estar vacía.")
            return {}

        content_list = [
            getattr(doc, "content", "").strip()
            for doc in docs
            if getattr(doc, "content", "").strip()
        ]

        if not content_list:
            logging.error("No se encontraron documentos con contenido válido.")
            return "No hay contenido válido para generar un resumen."

        MAX_ATTEMPTS = 3
        attempt = 0
        success = False
        response = {
            "summary": "Error en la generación del resumen tras múltiples intentos."
        }
        while attempt < MAX_ATTEMPTS and not success:
            try:
                prompt = [
                    {
                        "role": "system",
                        "content": prompt_template["system"],
                    },
                    {
                        "role": "user",
                        "content": prompt_template["user"].format(
                            contents=content_list, query=query
                        ),
                    },
                ]

                output = await self.llm_service.generate_text(
                    [prompt], max_new_tokens=5000
                )
                summary = output[0]
                if isinstance(summary, str):
                    response = {"summary": summary}
                    success = True
                else:
                    logging.warning(
                        f"Formato inesperado en la respuesta del modelo. Output: {output}"
                    )
                    attempt += 1

            except Exception as e:
                logging.error(
                    f"Error generando resumen para la query '{query}' (Intento {attempt + 1}): {e}"
                )
                attempt += 1

        return response

    async def apply_prompt_summary(
        self, docs: List[dict], prompt_template: dict
    ) -> Dict[str, str]:
        if not docs:
            logging.error("La lista de documentos no puede estar vacía.")
            return {}

        content_list = [
            getattr(doc, "content", "").strip()
            for doc in docs
            if getattr(doc, "content", "").strip()
        ]

        if not content_list:
            logging.error("No se encontraron documentos con contenido válido.")
            return "No hay contenido válido para generar un resumen."

        MAX_ATTEMPTS = 3
        attempt = 0
        success = False
        response = {
            "summary": "Error en la generación del resumen tras múltiples intentos."
        }
        while attempt < MAX_ATTEMPTS and not success:
            try:
                prompt = [
                    {
                        "role": "system",
                        "content": prompt_template["system"],
                    },
                    {
                        "role": "user",
                        "content": prompt_template["user"].format(
                            contents=content_list
                        ),
                    },
                ]

                output = await self.llm_service.generate_text(
                    [prompt], max_new_tokens=5000
                )
                summary = output[0]

                if isinstance(summary, str):
                    response = {"summary": summary}
                    success = True
                else:
                    logging.warning(
                        f"Formato inesperado en la respuesta del modelo. Output: {output}"
                    )
                    attempt += 1

            except Exception as e:
                logging.error(f"Error generando resumen (Intento {attempt + 1}): {e}")
                attempt += 1

        return response

    ##########################################
    async def get_dates(self, user_input: str):
        """
        Usa function calling para obtener el rango de fechas a partir del input.
        Si el input contiene una expresión relativa (por ejemplo, "últimas 4 semanas" o "últimos 50 días"),
        se invoca la tool 'get_relative_dates'. Si contiene fechas fijas, se invoca 'get_fixed_dates'.
        Se retorna una tupla (since_date, to_date) en formato YYYY-MM-DD.
        """
        # Definir las tools para calcular fechas:
        dates_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_relative_dates",
                    "description": "Get the dates to establish the 'since' and 'to' values from a relative expression. Example: 'last 4 weeks', 'last 50 days'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "time_unit": {
                                "type": "string",
                                "description": "The time unit expressed in the input. Example: Days, Weeks, Months, Years.",
                            },
                            "time_unit_value": {
                                "type": "integer",
                                "description": "The numeric value of the time unit. Example: 4 for 'last 4 weeks'.",
                            },
                        },
                        "required": ["time_unit", "time_unit_value"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_fixed_dates",
                    "description": "Get the 'since' and 'to' dates from a fixed expression. Example: '2025-03-01' to '2025-03-06'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "since_date": {
                                "type": "string",
                                "description": "The start date in the format YYYY-MM-DD.",
                            },
                            "to_date": {
                                "type": "string",
                                "description": "The end date in the format YYYY-MM-DD.",
                            },
                        },
                        "required": ["since_date", "to_date"],
                    },
                },
            },
        ]

        messages = [{"role": "user", "content": user_input}]

        raw_response = await self.llm_service.generate_function_call(
            messages, dates_tools
        )
        if isinstance(raw_response, str):
            try:
                json_response = self._parse_model_response(raw_response)
            except Exception as e:
                logging.warning(f"Error al parsear la respuesta: {e}")
                json_response = None

        tool_name = json_response.get("name", "").lower()
        params = json_response.get("parameters", {})

        if tool_name == "get_relative_dates":
            # Aquí usamos cálculo local para mayor precisión.
            time_unit = params.get("time_unit", "").lower()
            raw_time_unit_value = params.get("time_unit_value", 0)
            try:
                time_unit_value = int(raw_time_unit_value)
            except (TypeError, ValueError):
                logger.warning(
                    f"Valor de time_unit_value no es un entero válido: {raw_time_unit_value!r}, usando 0."
                )
                time_unit_value = 0

            current_date = datetime.now()
            if time_unit == "days":
                since_date = (current_date - timedelta(days=time_unit_value)).strftime(
                    "%Y-%m-%d"
                )
            elif time_unit == "weeks":
                since_date = (current_date - timedelta(weeks=time_unit_value)).strftime(
                    "%Y-%m-%d"
                )
            elif time_unit == "months":
                since_date = (
                    current_date - relativedelta(months=time_unit_value)
                ).strftime("%Y-%m-%d")
            elif time_unit == "years":
                since_date = (
                    current_date - relativedelta(years=time_unit_value)
                ).strftime("%Y-%m-%d")
            else:
                since_date = current_date.strftime("%Y-%m-%d")
            to_date = current_date.strftime("%Y-%m-%d")
            return since_date, to_date

        elif tool_name == "get_fixed_dates":
            since_date = params.get("since_date", datetime.now().strftime("%Y-%m-%d"))
            to_date = params.get("to_date", datetime.now().strftime("%Y-%m-%d"))
            return since_date, to_date
        else:
            # Fallback: usar últimos 7 días
            since_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            to_date = datetime.now().strftime("%Y-%m-%d")
            return since_date, to_date

    async def apply_function_calling(self, user_input: str) -> str:
        """
        Flujo multi-paso:
          1. Se obtiene el rango de fechas (since_date, to_date) a partir del input,
             usando las tools 'get_relative_dates' o 'get_fixed_dates' según corresponda.
          2. Se utiliza el rango obtenido y se extrae el contenido relevante para la query.
          3. Se invoca la tool 'get_summary' con el rango y el query_content.
          4. Se retorna la respuesta final en formato JSON.
        """
        # Obtener el rango de fechas.
        since_date, to_date = await self.get_dates(user_input)
        logger.info(f"##########Fechas obtenidas: desde {since_date} hasta {to_date}.")
        # Armar el mensaje final que se enviará a la tool 'get_summary'.
        messages_summary = [
            {
                "role": "user",
                "content": user_input
                + f"Date range: since_date: {since_date}. to_date: {to_date}.",
            }
        ]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_summary",
                    "description": "Generate a summary for a specific topic or index within a given date range.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "since_date": {
                                "type": "string",
                                "description": "The start date for the summary period in the format YYYY-MM-DD.",
                            },
                            "to_date": {
                                "type": "string",
                                "description": "The end date for the summary period in the format YYYY-MM-DD.",
                            },
                            "query_content": {
                                "type": "string",
                                "description": "The query content to be used in the Elasticsearch query (i.e. the text after 'content:' used to filter documents). Example: 'luisa OR gonzalez OR \"luisa gonzalez\" AND elecciones'.",
                            },
                        },
                        "required": ["since_date", "to_date", "query_content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_docs",
                    "description": "Retrieve raw documents for a specific topic or index within a given date range.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "since_date": {
                                "type": "string",
                                "description": "The start date for the period in which to retrieve documents, formatted as YYYY-MM-DD.",
                            },
                            "to_date": {
                                "type": "string",
                                "description": "The end date for the period in which to retrieve documents, formatted as YYYY-MM-DD.",
                            },
                            "query_content": {
                                "type": "string",
                                "description": "The query content to be used in the Elasticsearch query (i.e. the text after 'content:' used to filter documents). Example: 'luisa OR gonzalez OR \"luisa gonzalez\" AND elecciones'.",
                            },
                        },
                        "required": ["since_date", "to_date", "query_content"],
                    },
                },
            },
        ]
        logger.info(f"########## Haciendo segunda llamada")
        raw_response = await self.llm_service.generate_function_call(
            messages_summary, tools
        )

        # parsed_response = self._parse_function_call_response(raw_response)

        # 5. Retornar la respuesta final.
        return raw_response

        # def get_dates(input):
        #     dates_tools = [
        #             {
        #                 "type": "function",
        #                 "function": {
        #                     "name": "get_relative_dates",
        #                     "description": "Get the date to estabish the 'since' and 'to' dates for the query from a relativ expression. Example 'last 4 weeks', 'last year'.",
        #                     "parameters": {
        #                         "type": "object",
        #                         "properties": {
        #                             "time_unit": {
        #                                 "type": "str",
        #                                 "description": "The time unit expressed in the input. Example: Hours, Days, Weeks, Months, Years."
        #                             },
        #                             "time_unit_value": {
        #                                 "type": "integer",
        #                                 "description": "The value of the time unit expressed in the input. Example: 1, 2, 3."
        #                             }
        #                         },
        #                         "required": ["time_unit", "time_unit_value"]
        #                     }
        #                 }
        #             },
        #             {
        #                 "type": "function",
        #                 "function": {
        #                     "name": "get_fixed_dates",
        #                     "description": "Get the date to estabish the 'since' and 'to' dates for the query from a fixed expression. Example '2023-01-01', '2023-12-31'.",
        #                     "parameters": {
        #                         "type": "object",
        #                         "properties": {
        #                             "since_date": {
        #                                 "type": "string",
        #                                 "description": "The start date for the summary period in the format YYYY-MM-DD."
        #                             },
        #                             "to_date": {
        #                                 "type": "string",
        #                                 "description": "The end date for the summary period in the format YYYY-MM-DD."
        #                             }
        #                         },
        #                         "required": ["since_date", "to_date"]
        #                     }
        #                 }
        #             }
        #         ]
        #     raw_response = await self.llm_service.generate_function_call(messages, dates_tools)

        #     def get_relative_dates(response):
        #         # Parse the input to extract the time unit and value
        #         time_unit = response.get("time_unit")
        #         time_unit_value = response.get("time_unit_value")
        #         current_date = get_current_date()

        #         since_date = get_since_date(time_unit, time_unit_value)
        #         to_date = current_date
        #         return since_date, to_date

        #     def get_current_date():
        #         from datetime import datetime
        #         return datetime.now().strftime("%Y-%m-%d")

        #     def get_since_date(time_unit, time_unit_value):
        #         from datetime import datetime, timedelta
        #         current_date = datetime.now()
        #         if time_unit.lower() == "days":
        #             return (current_date - timedelta(days=time_unit_value)).strftime("%Y-%m-%d")
        #         elif time_unit.lower() == "weeks":
        #             return (current_date - timedelta(weeks=time_unit_value)).strftime("%Y-%m-%d")
        #         elif time_unit.lower() == "months":
        #             return (current_date - timedelta(days=30*time_unit_value)).strftime("%Y-%m-%d")
        #         elif time_unit.lower() == "years":
        #             return (current_date - timedelta(days=365*time_unit_value)).strftime("%Y-%m-%d")
        #         else:
        #             raise ValueError("Invalid time unit.")

        #     def get_fixed_dates(response):
        #         since_date = response.get("since_date")
        #         to_date = response.get("to_date")
        #         return since_date, to_date

        #     tool_answers = [
        #         tool_funtions[call['name']](**call['arguments']) for call in raw_response
        #     ]

        #     return tool_answers
