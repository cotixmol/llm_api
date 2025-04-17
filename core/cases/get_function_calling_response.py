from api.dtos.responses_dtos import FunctionCallingResponse
from pydantic import BaseModel
from typing import List
from core.cases.get_summary_response import GetSummaryResponseCase
import json
from api.config.logger import logger  



class GetFunctionCallingCase:
    def __init__(self, llm_repository, user_input: str,
                 query_repository, es_repository, index_pattern: str = "in-*"
                 ):
        self.llm_repository = llm_repository
        self.user_input = user_input
        self.query_repository = query_repository
        self.es_repository = es_repository
        self.index_pattern = index_pattern


    function_to_case = {
        "get_summary": GetSummaryResponseCase,
        # "get_docs":    GetDocsResponseCase
    }
    
    ####PROVISORIO
    summary_prompt = {
                "system": "You are an AI assistant specialized in summarizing large amounts of text into concise and structured bullet points.",
                "user": """
                        Below are documents from diverse social media.  
                        Each document contains relevant information for this topic.

                        {contents}

                        Based on these documents, generate a summary with the most relevant points in bullet point format:
                        - Point 1
                        - Point 2
                        - Point 3
                        - ...

                        Your answer must be in spanish and must be just the category as the title, and the summarized points below. Do not repeat information.
                        """
                }

    def get_endpoint_and_parameters(self, response):
        # Parse the response to extract the function name and parameters
        if isinstance(response, str):
           try:
               response = json.loads(response)
           except json.JSONDecodeError as e:
               logger.error(f"Error parseando response JSON: {e}")
               raise ValueError(f"Invalid JSON response from LLM: {e}")

        try:
            function_name = response.get("name")
            parameters = response.get("parameters")
            return function_name, parameters
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse response: {e}")

    async def __call__(self) -> FunctionCallingResponse:
        response = await self.llm_repository.apply_function_calling(user_input=self.user_input)
        logger.info(f"################Response: {response}")
        #Definir endpoint 
        function_name, parameters = self.get_endpoint_and_parameters(response)  
        logger.info(f"######Function name: {function_name}")
        logger.info(f"######Parameters: {parameters}")    
        if not parameters:
            raise ValueError("Missing parameters in the response.")
        # Llamar al caso correspondiente
        #PROVISORIO
        class ExtraArgs(BaseModel):
            fields: List[str]

        if function_name in self.function_to_case:
            case_class = self.function_to_case[function_name]
            case_instance = case_class(
                es_repository=self.es_repository,  
                query_repository=self.query_repository,
                llm_repository=self.llm_repository,
                index_pattern=self.index_pattern,
                since_date=parameters.get("since_date"),
                to_date=parameters.get("to_date"),
                extra_args=ExtraArgs(fields=["_id", "created_at", "category", "content_type", "author", "content", "source", "@timestamp"]),  
                prompt=self.summary_prompt,  
                max_ndocs=30,  
                batch_size=10,  
                query=parameters.get("query_content")
            )
            endpoint_result = await case_instance()  # Llamar al caso
        else:
            raise ValueError(f"Function {function_name} not supported.")
        # Retornar el resultado del caso
        #Acá puede hacerse otra llamada al modelo con la respuesta del endpoint que se llamó + la tool
        return FunctionCallingResponse(result=endpoint_result.model_dump())