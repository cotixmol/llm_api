from typing import List, Dict, Optional
from api.config.logger import logger
from V2.core.services.llm_service.llm_service import (
    LLMService,
    LLMException,
)

# Assuming your Document type is defined somewhere appropriate
from V2.core.objects.elastic_search_object import ElasticSearchDocument


class LLMServiceRepositoryV2:
    def __init__(self, llm_service: LLMService):
        """
        :param llm_service: An instance of LLMService.
        """
        self.llm_service = llm_service

    async def classify_documents(
        self,
        prompt_template: Dict[str, str],
        task_key: str,
        update_field: str,
        valid_labels: List[str],
        batch_size: int,
        docs: List[ElasticSearchDocument],
    ) -> Dict[str, List]:
        """
        This method mimics the V1 `apply_prompt_classification` but in V2 style.
        It pre-processes documents, sends them in batches to the LLM service,
        and parses the responses.
        """
        if not docs:
            logger.error("Document list cannot be None or empty.")
            raise ValueError("No documents provided for classification.")
        if (
            not prompt_template
            or "system" not in prompt_template
            or "user" not in prompt_template
        ):
            logger.error("Prompt template is missing required fields.")
            raise ValueError("Invalid prompt template provided.")

        # Preprocess: extract content and track skipped documents.
        es_index_list = []
        doc_id_list = []
        content = []
        skipped_es_index_list = []
        skipped_doc_id_list = []
        skipped_category = []

        for doc in docs:
            # Using document content if available, otherwise default to "empty"
            doc_content = doc.content if doc.content else "empty"
            if not doc_content or doc_content.strip() == "" or doc_content == "empty":
                skipped_es_index_list.append(doc.index)
                skipped_doc_id_list.append(doc.id)
                skipped_category.append({task_key: None})
                continue
            content.append(doc_content)
            es_index_list.append(doc.index)
            doc_id_list.append(doc.id)

        if not content:
            raise ValueError("No valid documents found for classification.")

        pending_indices = list(range(len(content)))
        predictions = [None] * len(content)
        max_attempts = 3

        for attempt in range(max_attempts):
            if not pending_indices:
                break

            logger.info(
                f"Attempt {attempt + 1}: Processing {len(pending_indices)} pending documents."
            )
            for i in range(0, len(pending_indices), batch_size):
                batch_indices = pending_indices[i : i + batch_size]
                batch_prompts = self._build_batch_prompts(
                    prompt_template, content, batch_indices
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
                            f"Doc index {idx} (id: {doc_id_list[idx]}) generated text: {generated_text}"
                        )
                        parsed = self._parse_model_response(
                            generated_text, valid_labels, task_key
                        )
                        if not isinstance(parsed, dict):
                            logger.warning(
                                f"Unexpected response format for doc index {idx}: {parsed}"
                            )
                            continue
                        if task_key not in parsed:
                            logger.warning(
                                f"Missing key '{task_key}' in response for doc index {idx}"
                            )
                            continue
                        predictions[idx] = parsed[task_key]
                    except Exception as parse_error:
                        logger.error(
                            f"Error processing document index {idx}: {parse_error}",
                            exc_info=True,
                        )

            pending_indices = [
                idx for idx in pending_indices if predictions[idx] is None
            ]

        for idx in pending_indices:
            logger.error(
                f"Document discarded after {max_attempts} attempts: {content[idx]}"
            )

        category_list = [{update_field: prediction} for prediction in predictions]

        return {
            "es_index_list": es_index_list + skipped_es_index_list,
            "doc_id_list": doc_id_list + skipped_doc_id_list,
            "classification_list": category_list + skipped_category,
        }

    def _build_batch_prompts(
        self,
        prompt_template: Dict[str, str],
        content: List[str],
        batch_indices: List[int],
    ) -> List[List[Dict[str, str]]]:
        """
        Build prompts for a given batch using the provided template.
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
        Parse the generated text and match it against valid labels.
        """
        for label in valid_labels:
            if label.lower() in response_text.lower():
                return {task_key: label}
        return {}
