from typing import List, Dict
from services.llm_vllm_service import LLMService
from api.dtos.responses_dtos import FunctionCallingResponse
from core.repositories.llm_repository import LLMRepository



class GetFunctionCallingCase:
    def __init__(self, llm_repository, user_input: str):
        self.llm_repository = llm_repository
        self.user_input = user_input

    async def __call__(self) -> FunctionCallingResponse:
        response = await self.llm_repository.apply_function_calling(input=self.user_input)
        #endpoint = funcion_para_saber_que_endpoint_llamar(response)
        #endpoint_result = funcion_para_llamar_al_endpoint_correspondiente(endpoint)
        #Acá puede hacerse otra llamada al modelo con la respuesta del endpoint que se llamó + la tool
        return FunctionCallingResponse(result=response)
