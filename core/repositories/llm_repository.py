import typing
import json
import logging
from services.llm_service import LLMService
from typing import List, Dict
from collections import defaultdict

class LLMRepository:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    @staticmethod
    def parse_model_response(response_text: str, valid_labels: typing.List[str]) -> typing.Optional[dict]:
        try:
            start_index = response_text.find('{')
            end_index = response_text.rfind('}') + 1
            json_text = response_text[start_index:end_index]
            response_data = json.loads(json_text)
            
            # Validar que el valor de la clave 'task_key' esté en las etiquetas válidas
            for key, value in response_data.items():
                if value not in valid_labels:
                    logging.warning(f"Etiqueta no válida '{value}' para la clave '{key}'.")
                    return None
            return response_data
        except (ValueError, json.JSONDecodeError):
            logging.warning(f"Formato incorrecto en la respuesta del modelo. Response: {response_text}")
            return None
    

    async def create_topic_name_and_summary(self,
                                    num_keywords: int = 8, 
                                    num_docs: int = 8, 
                                    keywords: typing.List[str] = None, 
                                    docs_list: typing.List[str] = None) -> typing.Tuple[str, str]:
        if keywords is None or docs_list is None:
            logging.error("Keywords y docs_list no pueden ser None")
            return None, None


        MAX_ATTEMPTS = 6 
        index = 0

        for attempt in range(MAX_ATTEMPTS):
            if attempt < 3:
                docs_to_use = docs_list[:min(num_docs, len(docs_list))]
                keywords_to_use = keywords[:min(num_keywords, len(keywords))]
            else:
                index += 3
                docs_to_use = docs_list[index:min(index+num_docs, len(docs_list))]  
                keywords_to_use = keywords[index:min(index+num_keywords, len(keywords))]

            prompt = f"""
            Existe un tópico compuesto a partir de las siguientes palabras claves: {keywords_to_use}
            Los siguientes documentos son un pequeño pero representativo subconjunto de todos los documentos pertenecientes al tópico:
            {docs_to_use}

            Basado en la información anterior, genera un nombre corto o etiqueta para el tópico y una descripción breve (máximo 3 oraciones). Debes responder en formato JSON, según la siguiente estructura:
            {{
                "topic_name": "<nombre>",
                "topic_description": "<descripción>"
            }}
            """

            messages = [
            {"role": "user", "content": prompt},
            ]

            try:
                outputs = await self.llm_service.generate_text(messages, max_new_tokens=350)

                response_data = self.parse_model_response(outputs[-1]["content"])

                try:
                    topic_name = response_data["topic_name"]
                    topic_description = response_data["topic_description"]
                    return topic_name, topic_description
                except:
                    logging.warning(f"Formato incorrecto en la respuesta del modelo, intento número {attempt + 1}. Response: {response_data}")
            
            except:
                logging.warning(f"Error en la generación de Nombre y Tópico, intento número {attempt + 1}")

        logging.error(f"No se pudo generar una respuesta válida después de {MAX_ATTEMPTS} intentos")
        return None, None   
    
    async def apply_prompt_classification(
        self,
        prompt_template: typing.Dict[str, str],
        task_key: str,
        update_field: str,
        valid_labels: typing.List[str],
        docs: List[dict] = None,
        batch_size: int = 2,
    ) -> typing.List[typing.Dict[str, typing.Optional[str]]]:
        
        if not docs:
            logging.error("docs_list no puede ser None o vacío.")
            return []
        if not prompt_template:
            logging.error("El template de prompt no puede ser None o vacío.")
            return []
        
        es_index_list = [] #Se puede tener más de un índice?
        doc_id_list = []
        content = []
        skiped_es_index_list = []#idem
        skiped_doc_id_list = []
        skiped_category = []

        predictions = [None] * len(docs)
        pending_indices = list(range(len(docs))) 

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

        for attempt in range(5): 
            if not pending_indices:
                break 

            logging.info(f"Intento {attempt + 1} con {len(pending_indices)} documentos pendientes.")

            # iteramos sobre batches de documentos de tamaño batch_size    
            for i in range(0, len(pending_indices), batch_size):
                batch_indices = pending_indices[i:i + batch_size]
                #batch_prompts = List[List[Dict[str, str]]]
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
                    outputs = await self.llm_service.generate_text(batch_prompts, max_new_tokens=40)
                except Exception as batch_error:
                    logging.error(f"Error procesando el batch {i // batch_size + 1}: {batch_error}")


                for idx, output in zip(batch_indices, outputs):
                    try:
                        # Validar si el output es una lista y contiene al menos un elemento
                        if not isinstance(output, list) or len(output) == 0:
                            logging.warning(f"Output inesperado para el documento {idx}. Output: {output}")
                            continue

                        # Validar si el primer elemento contiene la clave 'generated_text'
                        if 'generated_text' not in output[0]:
                            logging.warning(f"El output no contiene 'generated_text' para el documento {idx}. Output: {output[0]}")
                            continue

                        generated_text = output[0]['generated_text']
                        logging.debug(f"Texto generado para el documento {idx}: {generated_text}")

                        # Parsear el texto generado
                        response_data = self.parse_model_response(generated_text, valid_labels)

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


            pending_indices = [idx for idx in pending_indices if predictions[idx] is None]

        for idx in pending_indices:
            logging.error(f"Documento descartado tras 5 intentos: {doc_content[idx]}")

        category_list = [{update_field: prediction} for prediction in predictions]

        return {
        "es_index_list": es_index_list + skiped_es_index_list,
        "doc_id_list": doc_id_list + skiped_doc_id_list,
        "classification_list": category_list + skiped_category
         }
    

    
    async def apply_prompt(self, prompt: typing.List[typing.Dict[str, str]]) -> typing.Optional[str]:
        attempts = 0
        while attempts < 5:
            try:
                output = await self.llm_service.generate_text(prompt, max_new_tokens=50)
                return output[-1]["generated_text"]
            except Exception as e:
                logging.error(f"Error generando texto en el intento {attempts + 1}: {e}")
                attempts += 1
        
        logging.error("Fallo en todos los intentos para generar texto.")
        return None
    

    
    async def apply_prompt_categories_summary(self, docs: List[dict], prompt_template: dict, summary_field: str) -> Dict[str, str]:
        if not docs:
            logging.error("La lista de documentos no puede estar vacía.")
            return {}

        # Agrupar documentos por el campo dinámico (summary_field), descartando los que no lo tengan
        category_docs = defaultdict(list)
        for doc in docs:
            category = getattr(doc, summary_field, None) 
            content = getattr(doc, "content", "").strip()
            
            # Si falta la categoría o el contenido está vacío, se descarta
            if not category or not content:
                logging.warning(f"Documento descartado: {doc}")  
                continue
            
            category_docs[category].append(content)
        # Limitar a 50 documentos por categoría
        for category in category_docs:
            category_docs[category] = category_docs[category][:50]

        summaries = {}
        MAX_ATTEMPTS = 3  # 🔹 Número máximo de intentos por categoría

        for category, contents in category_docs.items():
            attempt = 0
            success = False

            while attempt < MAX_ATTEMPTS and not success:
                try:
                    prompt = [
                        {
                            "role": "system",
                            "content": prompt_template["system"],
                        },
                        {
                            "role": "user",
                            "content": prompt_template["user"].format(contents=contents, category=category)
                        }
                    ]

                    output = await self.llm_service.generate_text(prompt, max_new_tokens=5000)

                    # Validar la respuesta del modelo antes de guardarla
                    if isinstance(output, list) and output and 'generated_text' in output[-1]:
                        summaries[category] = output[-1]['generated_text']
                        success = True  
                    else:
                        logging.warning(f"Formato inesperado en la respuesta del modelo para '{category}'. Output: {output}")
                        attempt += 1

                except Exception as e:
                    logging.error(f"Error generando resumen para '{category}' (Intento {attempt + 1}): {e}")
                    attempt += 1  

            # Si después de varios intentos sigue fallando, guardar un mensaje de error
            if not success:
                summaries[category] = "Error en la generación del resumen tras múltiples intentos."

        return summaries
    

    async def apply_prompt_query_summary(self, docs: List[dict], prompt_template: dict, query: str) -> Dict[str, str]:
        if not docs:
            logging.error("La lista de documentos no puede estar vacía.")
            return {}
         
        content_list = [getattr(doc, "content", "").strip() for doc in docs if getattr(doc, "content", "").strip()][:50]

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
                
                output = await self.llm_service.generate_text(prompt, max_new_tokens=5000)
                
                if isinstance(output, list) and output and 'generated_text' in output[-1]:
                    response = {"summary": output[-1]['generated_text']}
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
         
        content_list = [getattr(doc, "content", "").strip() for doc in docs if getattr(doc, "content", "").strip()][:50]

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
                
                output = await self.llm_service.generate_text(prompt, max_new_tokens=5000)
                
                if isinstance(output, list) and output and 'generated_text' in output[-1]:
                    response = {"summary": output[-1]['generated_text']}
                    success = True  
                else:
                    logging.warning(f"Formato inesperado en la respuesta del modelo. Output: {output}")
                    attempt += 1

            except Exception as e:
                logging.error(f"Error generando resumen (Intento {attempt + 1}): {e}")
                attempt += 1  

        return response