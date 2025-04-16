import typing
import json
import logging
from services.llm_vllm_service import LLMService
from core.objects.document import Document
from typing import List, Dict
from api.config.logger import logger
import json
import re
import logging

class LLMRepository:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    @staticmethod
    def _parse_model_response(response_text: str, valid_labels: typing.Optional[List[str]] = None) -> typing.Optional[dict]:
        """
            checks if the response_text is a valid json and if the value of the key 'task_key' is in the valid_labels
        """
        try:
            start_index = response_text.find('{')
            end_index = response_text.rfind('}') + 1
            json_text = response_text[start_index:end_index]
            response_data = json.loads(json_text)
            
            # Validar que el valor de la clave 'task_key' esté en las etiquetas válidas
            if valid_labels:
                for key, value in response_data.items():
                    if value not in valid_labels:
                        logging.warning(f"Etiqueta no válida '{value}' para la clave '{key}'.")
                        return None
            return response_data
        except (ValueError, json.JSONDecodeError):
            logging.warning(f"Formato incorrecto en la respuesta del modelo. Response: {response_text}")
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
            start_index = response_text.find('{')
            end_index = response_text.rfind('}') + 1
            json_text = response_text[start_index:end_index]
            response_data = json.loads(json_text)
            if "category" in response_data and "summary" in response_data:
                return {response_data["category"]: response_data["summary"]}
            else:
                logging.warning(
                    f"El JSON parseado no tiene el formato esperado. Claves encontradas: {list(response_data.keys())}. Response: {json_text}"
                )
        except (ValueError, json.JSONDecodeError) as e:
            logging.warning(f"Fallo en el método original de parseo: {e}. Response: {response_text}")

        # Segundo intento: enfoque robusto
        # Eliminar delimitadores de código (por ejemplo, ```json y ```)
        cleaned_text = re.sub(r"```(?:json)?", "", response_text, flags=re.IGNORECASE).strip()
        cleaned_text = cleaned_text.strip("`").strip()

        # Buscar un bloque JSON usando regex que capture todo el contenido entre llaves
        match = re.search(r"({.*})", cleaned_text, re.DOTALL)
        if not match:
            logging.warning(f"No se encontró un bloque JSON en la respuesta del modelo. Response: {response_text}")
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
            logging.warning(f"Fallo al parsear JSON en el segundo intento: {e}. Intentando limpieza adicional. Texto: {json_text}")
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
                logging.warning(f"Fallo final en el segundo intento tras limpieza adicional: {e2}. Response: {json_text_clean}")
                # Continuamos con el tercer intento

        # Tercer intento: tratamiento de comillas simples
        # Se intenta reemplazar de forma cuidadosa las comillas simples por dobles en el JSON extraído.
        # Esta transformación se aplica solo en el bloque obtenido tras la limpieza adicional.
        json_text_for_quotes = json_text if 'json_text_clean' not in locals() else json_text_clean
        # Usamos una regex para reemplazar comillas simples que rodean claves o valores, asumiendo que no forman parte del contenido interno.
        json_text_quotes = re.sub(
            r"(?<=[:{,])\s*'([^']+?)'\s*(?=[,}])",
            r' "\1" ',
            json_text_for_quotes
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
            logging.warning(f"Fallo final al parsear JSON tras corrección de comillas: {e3}. Response: {json_text_quotes}")
            return None
    
    async def create_topics_name_and_summary(            
        self,
        inference_data: typing.Dict[int, dict],
        num_keywords: int = 8,
        num_docs: int = 8
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
                    docs_to_use = data["docs"][:min(num_docs, len(data["docs"]))]
                    keywords_to_use = data["keywords"][:min(num_keywords, len(data["keywords"]))]
                else:
                    index += 3
                    docs_to_use = data["docs"][index:min(index+num_docs, len(data["docs"]))]  
                    keywords_to_use = data["keywords"][index:min(index+num_keywords, len(data["keywords"]))]
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
                                        """
                        }
                    ]
                    prompts.append(prompt)
                    topics_batch.append(topic)
                    
                except Exception as e:
                    logging.error(f"Error al generar el prompt para el tópico '{topic}': {e}")
                    continue

            response = await self.llm_service.generate_text(prompts, max_new_tokens=5000, batch_size=8)
            logger.debug(f"response: {response}")
            # Validar la respuesta del modelo antes de guardarla
            for topic, block in zip(topics_batch, response["outputs"]):
                topic_summary = block["text"]
                if isinstance(topic_summary, str):
                    try:
                        response_data = self._parse_model_response(topic_summary)
                        if response_data and "topic_name" in response_data and "topic_description" in response_data:
                            results[topic] = {
                            "name": response_data["topic_name"],
                            "description": response_data["topic_description"]
                        }
                        else:
                            logging.warning(f"Tópico {topic}: JSON sin las claves esperadas.")
                    except Exception as e:
                        logging.warning(f"Tópico {topic}: fallo al parsear la respuesta en el intento {attempt + 1}. Error: {e}")
                else:
                    logging.warning(f"Tópico {topic}: respuesta del modelo en formato inesperado en el intento {attempt + 1}.")
            
            # Actualizamos los tópicos pendientes
            pending_topics = [t for t in pending_topics if t not in results]
            attempt += 1

        #Informamos los tópicos a los que no se les pudo generar el informe
        for topic in pending_topics:
            logging.warning(f"El tópico '{topic}' no obtuvo un resumen válido tras {MAX_ATTEMPTS} intentos.")
        return results



        for attempt in range(MAX_ATTEMPTS):
            if attempt < 3:
                docs_to_use = docs_list[:min(num_docs, len(docs_list))]
                keywords_to_use = keywords[:min(num_keywords, len(keywords))]
            else:
                index += 3
                docs_to_use = docs_list[index:min(index+num_docs, len(docs_list))]  
                keywords_to_use = keywords[index:min(index+num_keywords, len(keywords))]

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
                outputs = await self.llm_service.generate_text(messages, max_new_tokens=350)
                response_data = self._parse_model_response(outputs[-1]["generated_text"])

                try:
                    topic_name = response_data["topic_name"]
                    topic_description = response_data["topic_description"]
                    return topic_name, topic_description
                except:
                    logging.warning(f"Formato incorrecto en la respuesta del modelo, intento número {attempt + 1}. Response: {response_data}")
            
            except Exception as e:
                logging.warning(f"Error en la generación de Nombre y Tópico, intento número {attempt + 1}. Error: {e}")

        logging.error(f"No se pudo generar una respuesta válida después de {MAX_ATTEMPTS} intentos")
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
            if not doc_content or doc_content=="empty":
                skiped_es_index_list.append(doc.index)
                skiped_doc_id_list.append(doc.id)
                skiped_category.append({
                    task_key: None
                })
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

            logging.info(f"Intento {attempt + 1} con {len(pending_indices)} documentos pendientes.")

            # iteramos sobre batches de documentos de tamaño batch_size    
            for i in range(0, len(pending_indices), batch_size):
                print(f"Procesando batch {i // batch_size + 1} de {len(pending_indices) // batch_size + 1}")
                batch_indices = pending_indices[i:i + batch_size]
                batch_prompts = [
                    [
                        {
                            "role": "system",
                            "content": prompt_template["system"],
                        },
                        {
                            "role": "user",
                            "content": prompt_template["user"].format(doc=content[idx])
                        }
                    ]
                    for idx in batch_indices
                ]

                try:
                    output = await self.llm_service.generate_text(batch_prompts, max_new_tokens=40)
                    responses = output
                except Exception as batch_error:
                    logging.error(f"Error procesando el batch {i // batch_size + 1}: {batch_error}")


                for idx, response in zip(batch_indices, responses):
                    try:
                        generated_text = response

                        # Parsear el texto generado
                        response_data = self._parse_model_response(generated_text, valid_labels)

                        # Validar si el response_data es un diccionario y contiene la clave esperada
                        if not isinstance(response_data, dict):
                            logging.warning(f"Formato inesperado del response_data para el documento {idx}. Response: {response_data}")
                            continue

                        if task_key not in response_data:
                            logging.warning(f"El response_data no contiene la clave '{task_key}' para el documento {idx}. Response: {response_data}")
                            continue

                        # Extraer la etiqueta y asignarla a las predicciones
                        label = response_data[task_key]
                        predictions[idx] = label
                        logging.info(f"Predicción exitosa para el documento {idx}: {label}")

                    except Exception as parse_error:
                        logging.error(f"Error al procesar el documento {idx}. Detalles: {parse_error}", exc_info=True)


            pending_indices = [idx for idx in pending_indices if not predictions[idx]]

        for idx in pending_indices:
            logging.error(f"Documento descartado tras 5 intentos: {content[idx]}")

        category_list = [{update_field: prediction} for prediction in predictions]

        return {
        "es_index_list": es_index_list + skiped_es_index_list,
        "doc_id_list": doc_id_list + skiped_doc_id_list,
        "classification_list": category_list + skiped_category
         }

    async def apply_prompt(self, prompt: list) -> str:
        attempts = 0
        prompt_message = [{"role": "user", "content": prompt}]
        while attempts < 5:
            try:
                output = await self.llm_service.generate_text([prompt_message], temperature=0, top_p=1, max_new_tokens=10)
                return output[0]
            except Exception as e:
                logging.error(f"Error generando texto en el intento {attempts + 1}: {e}")
                attempts += 1
        
        logging.error("Fallo en todos los intentos para generar texto.")
        return None
     
    async def apply_prompt_categories_summary(self, aggs: dict, prompt_template: dict, summary_field: str, batch_size: int) -> Dict[str, str]:
        buckets = (
            aggs
            .get("top_categories_hits", {})
            .get("buckets", [])
        )
        if not buckets:
            logging.error("No se encontraron buckets en la respuesta de Elasticsearch.")
            return {}

        # Para cada bucket se extraen los contenidos de los documentos (hits) de la subagregación 'top_interactions'
        category_docs = {}
        for bucket in buckets:
            # La categoría se obtiene directamente de la clave del bucket
            category = bucket.get("key")
            
            # Extraer los documentos del subbucket 'top_interactions'
            hits = (
                bucket
                .get("top_docs", {})
                .get("hits", {})
                .get("hits", [])
            )
            
            contents = []
            for hit in hits:
                source = hit.get("_source", {})
                # Se extrae y limpia el contenido
                content = source.get("content", "").strip()
                if not content:
                    logging.warning(f"Documento sin contenido en bucket '{category}': {hit}")
                    continue
                contents.append(content)
            
            if contents:
                # Limitar a 50 documentos por categoría
                category_docs[category] = contents[:50]
            else:
                logging.warning(f"No se encontraron contenidos válidos para la categoría '{category}'.")

        pending_categories = list(category_docs.keys())
        summaries = {}
        MAX_ATTEMPTS = 5
        attempt=0
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
                            "content": prompt_template["user"].format(contents=contents, category=category, summary_field=summary_field)
                        }
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
                            logging.warning(f"La categoría '{key}' nunca estuvo pendiente.")
            attempt += 1
        #Validamos que no existan resúmenes para categorías inventadas
        for key in list(summaries.keys()):
            if key.lower() not in [cat.lower() for cat in category_docs.keys()]:
                summaries.pop(key)
                logging.warning(f"La categoría '{key}' se removió porque no es una categoría válida.")

        #Informamos las categorías a las que no se les pudo generar el informe
        for category in category_docs.keys():
            if category.lower() not in [key.lower() for key in summaries.keys()]:
                logging.warning(f"La categoría '{category}' no obtuvo un resumen válido tras {MAX_ATTEMPTS} intentos.")


        return summaries
    
    async def apply_prompt_query_summary(self, docs: List[dict], prompt_template: dict, query: str) -> Dict[str, str]:
        if not docs:
            logging.error("La lista de documentos no puede estar vacía.")
            return {}
         
        content_list = [getattr(doc, "content", "").strip() for doc in docs if getattr(doc, "content", "").strip()]

        if not content_list:
            logging.error("No se encontraron documentos con contenido válido.")
            return "No hay contenido válido para generar un resumen."

        MAX_ATTEMPTS = 3
        attempt = 0
        success = False
        response = {"summary": "Error en la generación del resumen tras múltiples intentos."}
        while attempt < MAX_ATTEMPTS and not success:
            try:
                prompt = [
                    {
                        "role": "system",
                        "content": prompt_template["system"],
                    },
                    {
                        "role": "user",
                        "content": prompt_template["user"].format(contents=content_list, query=query)
                    }
                ]
                
                output = await self.llm_service.generate_text([prompt], max_new_tokens=5000)
                summary = output[0]
                if isinstance(summary, str):
                    response = {"summary": summary}
                    success = True  
                else:
                    logging.warning(f"Formato inesperado en la respuesta del modelo. Output: {output}")
                    attempt += 1

            except Exception as e:
                logging.error(f"Error generando resumen para la query '{query}' (Intento {attempt + 1}): {e}")
                attempt += 1  

        return response
    
    async def apply_prompt_summary(self, docs: List[dict], prompt_template: dict) -> Dict[str, str]:
        if not docs:
            logging.error("La lista de documentos no puede estar vacía.")
            return {}
         
        content_list = [getattr(doc, "content", "").strip() for doc in docs if getattr(doc, "content", "").strip()]

        if not content_list:
            logging.error("No se encontraron documentos con contenido válido.")
            return "No hay contenido válido para generar un resumen."

        MAX_ATTEMPTS = 3
        attempt = 0
        success = False
        response = {"summary": "Error en la generación del resumen tras múltiples intentos."}
        while attempt < MAX_ATTEMPTS and not success:
            try:
                prompt = [
                    {
                        "role": "system",
                        "content": prompt_template["system"],
                    },
                    {
                        "role": "user",
                        "content": prompt_template["user"].format(contents=content_list)
                    }
                ]
                
                output = await self.llm_service.generate_text([prompt], max_new_tokens=5000)
                summary = output[0]
                
                if isinstance(summary, str):
                    response = {"summary": summary}
                    success = True  
                else:
                    logging.warning(f"Formato inesperado en la respuesta del modelo. Output: {output}")
                    attempt += 1

            except Exception as e:
                logging.error(f"Error generando resumen (Intento {attempt + 1}): {e}")
                attempt += 1  

        return response

    async def apply_function_calling(self, input: str) -> str:
        """
        Arma la consulta al LLM integrando las tools predefinidas y realiza el llamado al método generate_function_call.
        """
        ##Alternativa para manejar las solicitudes con fechas relativas. Otra alternativa sería un doble llamado al LLM, uno para obtener la fecha y otro para el resumen.
        def get_current_date():
            from datetime import datetime
            return datetime.now().strftime("%Y-%m-%d")

        contextual_input = f"{input}. CONTEXTO: Fecha Actual: {get_current_date()}"
        messages = [{"role": "user", "content": contextual_input}]
        
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
                                "description": "The start date for the summary period in the format YYYY-MM-DD."
                            },
                            "to_date": {
                                "type": "string",
                                "description": "The end date for the summary period in the format YYYY-MM-DD."
                            },
                            "query_content": {
                                "type": "string",
                                "description": "The query content to be used in the Elasticsearch query (i.e. the text after 'content:' used to filter documents). Example: 'luisa OR gonzalez OR \"luisa gonzalez\" AND elecciones'."
                            }
                        },
                        "required": ["since_date", "to_date", "query_content"]
                    }
                }
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
                                "description": "The start date for the period in which to retrieve documents, formatted as YYYY-MM-DD."
                            },
                            "to_date": {
                                "type": "string",
                                "description": "The end date for the period in which to retrieve documents, formatted as YYYY-MM-DD."
                            }
                            "query_content": {
                                "type": "string",
                                "description": "The query content to be used in the Elasticsearch query (i.e. the text after 'content:' used to filter documents). Example: 'luisa OR gonzalez OR \"luisa gonzalez\" AND elecciones'."
                            }
                        },
                        "required": ["since_date", "to_date", "query_content"]
                    }
                }
            }
        ]
        
        raw_response = await self.llm_service.generate_function_call(messages, tools)
        
        #parsed_response = self._parse_function_call_response(raw_response)
        
        # 5. Retornar la respuesta final.
        return json.dumps(raw_response) 