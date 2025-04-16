from api.dtos.responses_dtos import FunctionCallingResponse
from core.cases.get_summary_response import GetSummaryResponseCase
import json



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
        try:
            function_name = response.get("name")
            parameters = response.get("parameters")
            return function_name, parameters
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse response: {e}")

    async def __call__(self) -> FunctionCallingResponse:
        response = await self.llm_repository.apply_function_calling(user_input=self.user_input)
        #Definir endpoint 
        function_name, parameters = self.get_endpoint_and_parameters(response)      
        if not parameters:
            raise ValueError("Missing parameters in the response.")
        # Llamar al caso correspondiente
        #PROVISORIO
        if function_name in self.function_to_case:
            case_class = self.function_to_case[function_name]
            case_instance = case_class(
                es_repository=self.es_repository,  
                query_repository=self.query_repository,
                llm_repository=self.llm_repository,
                index_pattern=self.index_pattern,
                since_date=parameters.get("since_date"),
                to_date=parameters.get("to_date"),
                extra_args={},  
                prompt=self.summary_prompt,  
                max_ndocs=100,  
                batch_size=10,  
                query=parameters.get("query_content")
            )
            endpoint_result = await case_instance()  # Llamar al caso
        else:
            raise ValueError(f"Function {function_name} not supported.")
        # Retornar el resultado del caso
        #Acá puede hacerse otra llamada al modelo con la respuesta del endpoint que se llamó + la tool
        return FunctionCallingResponse(result=endpoint_result)