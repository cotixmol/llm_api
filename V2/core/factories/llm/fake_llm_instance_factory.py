from types import SimpleNamespace
from typing import List, Dict
from faker import Faker

faker = Faker()


# ---- This should work as a fake library ----
class SamplingParams:
    def __init__(
        self,
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_tokens: int = 40,
    ) -> None:
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens


class FakeLLMLibrary:
    def __init__(self, *_, **__) -> None:
        pass

    def _fake_sentence(self, max_tokens: int) -> str:
        chars = 150
        return faker.text(max_nb_chars=chars).replace("\n", " ")

    def chat(
        self,
        requests: List[List[Dict[str, str]]],
        sampling_params: "SamplingParams",
    ):
        generations = []

        for _ in requests:
            fake_text = self._fake_sentence(sampling_params.max_tokens)
            gen = SimpleNamespace(outputs=[SimpleNamespace(text=fake_text)])
            generations.append(gen)

        return generations


# ---- This is the instanciation of the library ----


def initialize_fake_llm_instance():
    fake_llm_instance = FakeLLMLibrary()
    return fake_llm_instance
