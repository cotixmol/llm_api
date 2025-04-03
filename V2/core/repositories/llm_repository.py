import typing


class LLMRepositoryV2:
    # Duplicate of older LLM logic
    def __init__(self):
        pass

    async def apply_prompt_classification(
        self, docs: typing.List[dict], prompt_args: dict
    ) -> typing.List[dict]:
        # Stub method that simulates older LLM classification.
        # E.g. calling your LLM with the prompt
        # Return updated docs
        return [{"_id": d.get("_id"), "updated": True} for d in docs]
