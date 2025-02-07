from fastapi import Request
    
def get_llm_service(request: Request):
    return request.app.state.llm_service
    