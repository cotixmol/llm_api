from typing import List, Dict, Optional, Tuple
from api.config.logger import logger
from V2.core.services.llm_service.llm_service import LLMService, LLMException
from V2.core.objects.elastic_search_object import ElasticSearchDocument
from V2.api.dtos.classification_dto import BaseDocument
from V2.api.dtos.classification_dto import ClassificationRequest


class LLMServiceRepositoryV2:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    #
    async def classify_documents(
        self,
        docs: List[BaseDocument],
        request: ClassificationRequest,
    ) -> Dict[str, List]:
        """
        Refactored version of the classification method:
         1. Validate inputs.
         2. Pre-process documents: separate valid and skipped documents.
         3. Process valid documents in batches with retry logic.
         4. Assemble classification output preserving skipped entries.
        """
        self._validate_inputs(docs, request)
        valid_data, skipped_data = self._preprocess_documents(docs, request)

        if not valid_data["content"]:
            raise ValueError("No valid documents found for classification.")

        predictions = [None] * len(valid_data["content"])
        pending_indices = list(range(len(valid_data["content"])))
        max_attempts = 3  # Could be made configurable

        for attempt in range(max_attempts):
            if not pending_indices:
                break

            logger.info(
                f"Attempt {attempt + 1}: Processing {len(pending_indices)} pending documents."
            )
            pending_indices = await self._process_batches(
                pending_indices, valid_data, request, predictions
            )

        self._log_remaining(pending_indices, valid_data["content"])
        classification_list = self._build_classification_list(
            predictions, request.update_field
        )

        return {
            "index_list": valid_data["index_list"] + skipped_data["index_list"],
            "doc_id_list": valid_data["doc_id_list"] + skipped_data["doc_id_list"],
            "classification_list": classification_list + skipped_data["classification"],
        }

    def _validate_inputs(
        self, docs: List[BaseDocument], request: ClassificationRequest
    ):
        if not docs:
            logger.error("Document list cannot be None or empty.")
            raise ValueError("No documents provided for classification.")
        if (
            not request.prompt
            or "system" not in request.prompt
            or "user" not in request.prompt
        ):
            logger.error("Prompt template is missing required fields.")
            raise ValueError("Invalid prompt template provided.")

    def _preprocess_documents(
        self, docs: List[BaseDocument], request: ClassificationRequest
    ) -> Tuple[Dict[str, List], Dict[str, List]]:
        """
        Separates documents with valid content from those that should be skipped.
        """
        valid_data = {"index_list": [], "doc_id_list": [], "content": []}
        skipped_data = {"index_list": [], "doc_id_list": [], "classification": []}

        for doc in docs:
            if (doc.content or "empty").strip() in ("", "empty"):
                skipped_data["index_list"].append(doc.index)
                skipped_data["doc_id_list"].append(doc.id)
                skipped_data["classification"].append({request.task_key: None})
            else:
                valid_data["index_list"].append(doc.index)
                valid_data["content"].append(doc.content or "empty")
                valid_data["doc_id_list"].append(doc.id)

        return valid_data, skipped_data

    async def _process_batches(
        self,
        pending_indices: List[int],
        valid_data: Dict[str, List],
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
        for i in range(0, len(pending_indices), batch_size):
            batch_indices = pending_indices[i : i + batch_size]
            batch_prompts = self._build_batch_prompts(
                request.prompt, valid_data["content"], batch_indices
            )
            try:
                output = await self.llm_service.generate_text(
                    batch_prompts, max_new_tokens=40
                )
                responses = output.get("outputs", [])
            except Exception as batch_error:
                logger.error(
                    f"Error processing batch {(i // batch_size) + 1}: {batch_error}"
                )
                responses = []

            for idx, response in zip(batch_indices, responses):
                try:
                    generated_text = response.get("text", "")
                    logger.info(
                        f"Doc index {idx} (id: {valid_data['doc_id_list'][idx]}) generated text: {generated_text}"
                    )
                    parsed = self._parse_model_response(
                        generated_text, request.valid_labels, request.task_key
                    )
                    if not isinstance(parsed, dict) or request.task_key not in parsed:
                        logger.warning(
                            f"Unexpected response format for doc index {idx}: {parsed}"
                        )
                        continue
                    predictions[idx] = parsed[request.task_key]
                except Exception as parse_error:
                    logger.error(
                        f"Error processing document index {idx}: {parse_error}",
                        exc_info=True,
                    )

        # Update pending indices: keep those where no prediction was made
        return [idx for idx in pending_indices if predictions[idx] is None]

    def _log_remaining(self, pending_indices: List[int], contents: List[str]):
        for idx in pending_indices:
            logger.error(f"Document discarded after 3 attempts: {contents[idx]}")

    def _build_classification_list(
        self, predictions: List[Optional[str]], update_field: str
    ) -> List[Dict[str, Optional[str]]]:
        return [{update_field: prediction} for prediction in predictions]

    def _build_batch_prompts(
        self,
        prompt_template: Dict[str, str],
        content: List[str],
        batch_indices: List[int],
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
            for idx in batch_indices
        ]

    def _parse_model_response(
        self, response_text: str, valid_labels: List[str], task_key: str
    ) -> Dict:
        """
        Checks whether the generated text contains one of the valid labels.
        Returns a dictionary with the task_key mapped to the found label (or an empty dict if none match).
        """
        for label in valid_labels:
            if label.lower() in response_text.lower():
                return {task_key: label}
        return {}
