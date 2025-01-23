import typing
import json
import logging
from services.llm_service import LlmService

class LLMRepository:
    def __init__(self, llm_service: LlmService):
        self.llm_service = llm_service
    

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

                response_text = outputs[-1]["content"]

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
    
    def apply_prompt_classification(self, docs_list: typing.List[str] = None) -> str:
        predictions = []
        for doc in docs_list:
            topic_categories = """                  
                                    1)Category: RECIPES
                                    
                                    Definition: Posts related to the direct preparation of food or beverages.
                                    
                                    Key indicators:
                                    
                                    Includes ingredients and preparation steps.
                                    
                                    May mention cooking times/temperatures.
                                    
                                    Common phrases: "mix", "add", "bake", "recipe".
                                    
                                    Example:
                                    
                                    "Cake recipe: mix flour, eggs, and bake for 30 minutes." → RECIPES
                                    
                                    2)Category: NUTRITIONAL INFORMATION
                                    
                                    Definition: Informative content related to health and nutrition concepts.
                                    
                                    Key indicators:
                                    
                                    Explains the nutritional properties of foods or healthy habits.
                                    
                                    Use of scientific data or explicit health benefits.
                                    
                                    Common phrases: "benefits", "properties", "nutrition".
                                    
                                    Example:
                                    
                                    "Quinoa is rich in protein and contains all essential amino acids." → NUTRITIONAL INFORMATION
                                    
                                    3)Category: RECOMMENDATIONS
                                    
                                    Definition: Posts offering practical or promotional recommendations related to food, brands, or healthy lifestyles.
                                    
                                    Key indicators:
                                    
                                    Absence of detailed procedures or specific ingredients.
                                    
                                    General tips, organizational advice, or commercial mentions.
                                    
                                    Common phrases: "buy", "organize", "promotion".
                                    
                                    Example:
                                    
                                    "Buy seasonal fruits to save money and get better nutrients." → RECOMMENDATIONS
                                    
                                    4)Category: OTHERS
                                    
                                    Definition: Content not directly related to food preparation, nutrition, or practical recommendations.
                                    
                                    Key indicators:
                                    
                                    Focus on personal topics, landscapes, general events, or reflections unrelated to food topics.
                                    
                                    Example:
                                    
                                    "How beautiful the city is at this time of year." → OTHERS
            """
            prompt = {
                "system_1": f"""You are a text classifier analyzing social media posts. You must assign ONE category according to these definitions: {topic_categories}
                            Respond with one of the four categories (RECIPES, NUTRITIONAL INFORMATION, RECOMMENDATIONS, OTHERS) in JSON format: {{"type_of_posting": "CATEGORY"}}.

                            Rules:
                            1. Only ONE category per post
                            2. If more than one category applies, prioritize: RECIPES > NUTRITIONAL INFORMATION > RECOMMENDATIONS > OTHERS
                            3. Respond in JSON format: {{"type_of_posting": "CATEGORY"}}""",
                "user_1": f"Classify this post: {doc}"
            },

            try:
                outputs = self.llm_service.generate_text(prompt, max_new_tokens=350)
                response_text = outputs[-1]["content"]

                start_index = response_text.find('{')
                end_index = response_text.rfind('}') + 1
                json_text = response_text[start_index:end_index]
                try:
                    response_data = json.loads(json_text)
                    posting_type = response_data["posting_type"]
                    predictions.append(posting_type)
                except:
                    logging.warning(f"Formato incorrecto en la respuesta del modelo. Response: {response_text}")                
            except Exception as error:
                logging.error(f"Error generando texto: {error}")
                return None
            
    def apply_prompt(self, prompt):
        try:
                outputs = self.llm_service.generate_text(prompt, max_new_tokens=350)
                response_text = outputs[-1]["content"]
                return response_text
        except:
            logging.error(f"Error generando texto")
            return None


# Worker recibe tarea, manda prompt, filtros y reglas de ingesta (qué campo, etl) a endpoint, 
# API transforma (agregar métodos según uso), ingesta a elastic y envía reporte a worker

# Jinja para templates de prompts