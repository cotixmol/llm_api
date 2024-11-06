import typing
import re
import pickle

import torch
from transformers import pipeline

class LLMRepository:
    def __init__(self, model_path: str):    
        with open(model_path, 'rb') as pickle_file:
            model_data = pickle.load(pickle_file)

        self.model = model_data["model"]
        self.tokenizer = model_data["tokenizer"]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.pipeline = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer, device=self.device)

    def create_topic_name_and_summary(self,
                                      num_keywords: int, 
                                      num_docs: int, 
                                      keywords: typing.List[str], 
                                      docs_list: typing.List[str]) -> typing.Tuple[str, str]:
        docs_list = docs_list[:num_docs]
        keywords = keywords[:num_keywords]

        prompt = f"""
        Hay un tópico que está compuesto a partir de las siguientes palabras claves: {keywords}
        En este tópico, los siguientes documentos son un pequeño pero representativo subconjunto de todos los documentos del tópico:
        {docs_list}

        Basado en la información anterior, por favor extrae un nombre corto o etiqueta para el tópico y devuelve una descripción breve (máximo 3 oraciones) del mismo en el siguiente formato:
        Nombre del tópico: <nombre>
        Descripción del tópico: <descripción>
        """

        messages = [
            {"role": "user", "content": {prompt}},
        ]
        outputs = self.pipeline(
            messages,
            max_new_tokens=350,
        )
        response_text = (outputs[0]["generated_text"][-1]["content"])

        topic_name_match = re.search(r'Nombre del tópico:\s*(.*)', response_text)
        topic_name = topic_name_match.group(1).strip() if topic_name_match else None

        topic_description_match = re.search(r'Descripción del tópico:\s*(.*)', response_text)
        topic_description = topic_description_match.group(1).strip() if topic_description_match else None

        return topic_name, topic_description


