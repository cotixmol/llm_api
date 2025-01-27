import typing
import json
import logging
from services.llm_service import LLMService

class LLMRepository:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    @staticmethod
    def parse_model_response(response_text: str) -> typing.Optional[dict]:
        try:
            start_index = response_text.find('{')
            end_index = response_text.rfind('}') + 1
            json_text = response_text[start_index:end_index]
            return json.loads(json_text)
        except (ValueError, json.JSONDecodeError):
            logging.warning(f"Formato incorrecto en la respuesta del modelo. Response: {response_text}")
            return None
    

    def create_topic_name_and_summary(self,
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
                outputs = self.llm_service.generate_text(messages, max_new_tokens=350)

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
    
    async def apply_prompt_classification(self, prompt_template, task_key, docs_list: typing.List[str] = None) -> str: #BATCHES

        if not docs_list:
            logging.error("docs_list no puede ser None o vacío.")
            return []
        if not prompt_template:
            logging.error("El template de prompt no puede ser None o vacío.")
            return []

        predictions = []
        for doc in docs_list:
            prompt = prompt_template.format(doc=doc)
            attempts = 0
            success = False

            while attempts < 5 and not success:
                try:
                    outputs = await self.llm_service.generate_text(prompt, max_new_tokens=5)
                    try:
                        response_data = self.parse_model_response(outputs[-1]["content"])
                        label = response_data[task_key]
                        predictions.append(label)
                        success = True
                    except Exception as parse_error:
                        logging.warning(f"Formato incorrecto en la respuesta del modelo. Intento {attempts + 1}. Error: {parse_error}") #Debería chequearse no sólo la key, sino también el value. Tiene que venir lista de values válidos desde worker
                except Exception as error:
                    logging.error(f"Error generando texto en el intento {attempts + 1}: {error}")

                attempts += 1

            if not success:
                logging.error(f"Fallo procesando el documento tras 5 intentos. Documento descartado: {doc}") #cómo manejar los documentos descartados? Guardar indice?

        return predictions

    
    async def apply_prompt(self, prompt):
        attempts = 0
        while attempts < 5:
            try:
                output = await self.llm_service.generate_text(prompt, max_new_tokens=10)
                return output[-1]["generated_text"] 
            except Exception as e:
                logging.error(f"Error generando texto en el intento {attempts + 1}: {e}")
                attempts += 1
        
        logging.error("Fallo en todos los intentos para generar texto.")
        return None

