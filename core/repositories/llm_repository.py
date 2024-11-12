import typing
import pickle
import torch
from transformers import pipeline
import json
import logging

class LLMRepository:
    def __init__(self, model_path: str):    
        with open(model_path, 'rb') as pickle_file:
            model_data = pickle.load(pickle_file)

        self.model = model_data["model"]
        self.tokenizer = model_data["tokenizer"]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.pipeline = pipeline("text-generation", 
                                 model=self.model, 
                                 tokenizer=self.tokenizer, 
                                 device=self.device,
                                 torch_dtype=torch.bfloat16)

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
                docs_to_use = docs_list[:num_docs]
                keywords_to_use = keywords[:num_keywords]
            else:
                index += 4
                docs_to_use = docs_list[index:index+num_docs]  
                keywords_to_use = keywords[index:index+num_keywords]

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
                outputs = self.pipeline(
                    messages,
                    max_new_tokens=350,
                )
                response_text = outputs[0]["generated_text"][-1]["content"]

                start_index = response_text.find('{')
                end_index = response_text.rfind('}') + 1
                json_text = response_text[start_index:end_index]

                try:
                    response_data = json.loads(json_text)
                    topic_name = response_data["topic_name"]
                    topic_description = response_data["topic_description"]
                    return topic_name, topic_description
                except:
                    logging.warning(f"Formato incorrecto en la respuesta del modelo, intento número {attempt + 1}. Response: {response_text}")
            
            except:
                logging.warning(f"Error en la generación de Nombre y Tópico, intento número {attempt + 1}")

        logging.error(f"No se pudo generar una respuesta válida después de {MAX_ATTEMPTS} intentos")
        return None, None   
