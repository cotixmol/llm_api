from abc import ABC, abstractmethod


class TopicsModellingServiceRepositoryInterface(ABC):
    @abstractmethod
    async def get_topics() -> None:
        pass

    # @abstractmethod
    # async def method2() -> None:
    #     pass
