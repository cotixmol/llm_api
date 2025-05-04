from typing import List, Dict, Optional
import json
import re
from api.config.logger import logger
from V2.core.services.llm_service.vllm_service import VLLMService
from V2.api.dtos.common_dto import BaseDocument
from V2.api.dtos.classification_dto import ClassificationRequest
from V2.api.dtos.summary_dto import SummaryRequest


class VLLMServiceRepositoryV2:
    def __init__(self, llm_service: VLLMService):
        self.llm_service = llm_service

    async def classify_documents(
        self,
        documents: List[BaseDocument],
        request: ClassificationRequest,
    ) -> List[Dict]:
        """
        Refactored version of the classification method:
         1. Validate inputs.
         3. Process valid documents in batches with retry logic.
         4. Assemble classification output.
        """
        self._validate_inputs(documents, request)

        valid_data = {"content": [d.content or "empty" for d in documents]}

        if not valid_data["content"]:
            raise ValueError("No valid documents found for classification.")

        predictions = [None] * len(valid_data["content"])
        pending_indexes = list(range(len(valid_data["content"])))
        MAX_ATTEMPT = 3

        for attempt in range(MAX_ATTEMPT):
            if not pending_indexes:
                break

            logger.info(
                f"Attempt {attempt + 1}/{MAX_ATTEMPT}: Processing {len(pending_indexes)} pending documents."
            )
            pending_indexes = await self._process_batches(
                pending_indexes, valid_data, request, predictions
            )

        for idx in pending_indexes:
            logger.error(
                f"Document discarded after 3 attempts: {valid_data['content'][idx]}"
            )

        return [{request.update_field: p} for p in predictions]

    def _validate_inputs(
        self, documents: List[BaseDocument], request: ClassificationRequest
    ):
        if not documents:
            logger.error("Document list cannot be None or empty.")
            raise ValueError("No documents provided for classification.")
        if (
            not request.prompt
            or "system" not in request.prompt
            or "user" not in request.prompt
        ):
            logger.error("Prompt template is missing required fields.")
            raise ValueError("Invalid prompt template provided.")

    async def _process_batches(
        self,
        pending_indexes: List[int],
        valid_data: Dict[str, List[str]],
        request: ClassificationRequest,
        predictions: List[Optional[str]],
    ) -> List[int]:
        """
        Process the valid documents in batches:
         - Builds prompts for each batch.
         - Calls the LLM service and parses responses.
         - Updates the predictions list.
         Returns an updated list of pending document indices.
        """
        batch_size = request.batch_size
        for i in range(0, len(pending_indexes), batch_size):
            batch_indexes = pending_indexes[i : i + batch_size]
            batch_prompts = self._build_batch_prompts(
                request.prompt, valid_data["content"], batch_indexes
            )
            try:
                output = await self.llm_service.generate_text(batch_prompts)
                responses = output.get("outputs", [])
            except Exception as batch_error:
                logger.error(
                    f"Error processing batch {i // batch_size + 1}: {batch_error}",
                    exc_info=True,
                )
                responses = []

            for idx, response in zip(batch_indexes, responses):
                try:
                    generated_text = response.get("text", "")
                    logger.info(
                        f"Doc index {idx}: generated text: {generated_text} | "
                        f"Prompt time: {response['other_info']['prompt_time']}"
                    )
                    parsed = self._parse_model_response(
                        generated_text, request.valid_labels, request.task_key
                    )
                    if not isinstance(parsed, dict) or request.task_key not in parsed:
                        logger.warning(
                            f"Unexpected response format for doc index {idx}: {parsed}"
                        )
                        continue
                    predictions[idx] = parsed[
                        request.task_key
                    ]  # Update the mutable predictions list
                except Exception as parse_error:
                    logger.error(
                        f"Error processing document index {idx}: {parse_error}",
                        exc_info=True,
                    )

        # Update pending indices: keep those where no prediction was made
        return [idx for idx in pending_indexes if predictions[idx] is None]

    def _build_batch_prompts(
        self,
        prompt_template: Dict[str, str],
        content: List[str],
        batch_indexes: List[int],
    ) -> List[List[Dict[str, str]]]:
        """
        Build a list of prompt messages (each message is a list of dicts) for the given batch indices.
        """
        return [
            [
                {"role": "system", "content": prompt_template["system"]},
                {
                    "role": "user",
                    "content": prompt_template["user"].format(doc=content[idx]),
                },
            ]
            for idx in batch_indexes
        ]

    def _parse_model_response(
        self, response_text: str, valid_labels: List[str], task_key: str
    ) -> Dict:
        """
        Hybrid approach to extract a valid label from the response.
        First, it tries to parse a JSON block and check for an exact match.
        If that fails, it searches for a valid label as a substring.
        """
        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end != -1 and start < end:
                data = json.loads(response_text[start:end])
                for value in data.values():
                    if isinstance(value, str):
                        for label in valid_labels:
                            if value.lower() == label.lower():
                                return {task_key: label}
        except Exception as e:
            logger.warning(f"JSON parsing failed: {e}. Using substring matching.")

        for label in valid_labels:
            if label.lower() in response_text.lower():
                return {task_key: label}

        return {}

    def execute_prompt(
        self,
        prompt: str,
        max_new_tokens: Optional[int] = 1000,
        temperature: Optional[float] = 0.0,
        top_p: Optional[float] = 1.0,
    ) -> dict:
        """
        Execute a prompt using the LLM service.
        """
        prompt = [{"role": "user", "content": prompt}]
        try:
            return self.llm_service.generate_text(
                prompts=prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
            )
        except Exception as error:
            logger.error(f"Error executing prompt: {error}")
            raise VLLMServiceRepositoryV2(f"Error executing prompt: {error}")

    # ────────────────────────────────────────────────────────────────
    # PUBLIC API – called from SummaryRepository
    # ────────────────────────────────────────────────────────────────

    async def generate_summary(  # NEW PUBLIC METHOD
        self,
        documents: List[BaseDocument],
        request: SummaryRequest,
    ) -> Dict[str, str]:
        """
        Route the request to the correct summary strategy:
         • category‑based   (request.summary_field)
         • query‑focused    (request.query)
         • generic summary  (fallback)
        """
        if request.summary_field:
            return await self._summary_by_category(documents, request)
        if request.query:
            return await self._summary_by_query(documents, request)
        return await self._summary_generic(documents, request)

    # ────────────────────────────────────────────────────────────────
    # 1. CATEGORY SUMMARY  (equiv. to V1 apply_prompt_categories_summary)
    # ────────────────────────────────────────────────────────────────

    async def _summary_by_category(
        self,
        documents: List[BaseDocument],
        request: SummaryRequest,
    ) -> Dict[str, str]:
        cat_docs: Dict[str, List[str]] = defaultdict(list)
        for doc in documents:
            category = getattr(doc, request.summary_field, None)
            if category and doc.content:
                if len(cat_docs[category]) < 50:  # keep top‑50 per cat
                    cat_docs[category].append(doc.content.strip())

        pending = list(cat_docs.keys())
        summaries: Dict[str, str] = {}
        MAX_ATTEMPT = 5
        attempt = 0
        while pending and attempt < MAX_ATTEMPT:
            prompts = []
            for cat in pending:
                prompts.append(
                    [
                        {"role": "system", "content": request.prompt["system"]},
                        {
                            "role": "user",
                            "content": request.prompt["user"].format(
                                category=cat,
                                contents=cat_docs[cat],
                                summary_field=request.summary_field,
                            ),
                        },
                    ]
                )
            resp = await self.llm_service.generate_text(
                prompts, max_new_tokens=5000, batch_size=request.batch_size
            )
            for block in resp["outputs"]:
                parsed = self._parse_summary_response(block["text"])
                if parsed:
                    summaries.update(parsed)
            pending = [
                c for c in pending if c.lower() not in map(str.lower, summaries.keys())
            ]
            attempt += 1
        return summaries

    # ────────────────────────────────────────────────────────────────
    # 2. QUERY SUMMARY  (equiv. to V1 apply_prompt_query_summary)
    # ────────────────────────────────────────────────────────────────

    async def _summary_by_query(
        self,
        documents: List[BaseDocument],
        request: SummaryRequest,
    ) -> Dict[str, str]:
        contents = [d.content.strip() for d in documents if d.content]
        prompt = [
            {"role": "system", "content": request.prompt["system"]},
            {
                "role": "user",
                "content": request.prompt["user"].format(
                    contents=contents, query=request.query
                ),
            },
        ]
        resp = await self.llm_service.generate_text(prompt, max_new_tokens=5000)
        return {"summary": resp["outputs"][0]["text"]}

    # ────────────────────────────────────────────────────────────────
    # 3. GENERIC SUMMARY  (equiv. to V1 apply_prompt_summary)
    # ────────────────────────────────────────────────────────────────

    async def _summary_generic(
        self,
        documents: List[BaseDocument],
        request: SummaryRequest,
    ) -> Dict[str, str]:
        contents = [d.content.strip() for d in documents if d.content]
        prompt = [
            {"role": "system", "content": request.prompt["system"]},
            {
                "role": "user",
                "content": request.prompt["user"].format(contents=contents),
            },
        ]
        resp = await self.llm_service.generate_text(prompt, max_new_tokens=5000)
        return {"summary": resp["outputs"][0]["text"]}

    # ────────────────────────────────────────────────────────────────
    # Helper – JSON extractor reused by the three strategies
    # ────────────────────────────────────────────────────────────────

    def _parse_summary_response(self, response_text: str) -> Optional[Dict[str, str]]:
        """
        Very robust extractor:
        • finds the first {...} block that deserialises
        • accepts both ```json fenced blocks and plain text
        • tolerant to trailing commas / single quotes
        """
        try:
            # 1) quickly try naïve slice
            start, end = response_text.find("{"), response_text.rfind("}") + 1
            if start != -1 and end != -1 and start < end:
                data = json.loads(response_text[start:end])
                return (
                    {data["category"]: data["summary"]} if "category" in data else data
                )
        except Exception:
            pass

        # 2) clean md fences
        cleaned = re.sub(r"```(?:json)?", "", response_text, flags=re.I).strip("` \n")
        match = re.search(r"({.*})", cleaned, flags=re.S)
        if not match:
            return None
        block = match.group(1)
        for txt in (
            block,
            re.sub(r",\s*}", "}", block),
        ):  # try with / w.o. trailing commas
            try:
                data = json.loads(txt.replace("'", '"'))
                if isinstance(data, dict):
                    if "category" in data and "summary" in data:
                        return {data["category"]: data["summary"]}
                    return data
            except Exception:
                continue
        return None
