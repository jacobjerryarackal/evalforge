from abc import ABC, abstractmethod

from src.domain.entities.trajectory import Trajectory


class AgentSUT(ABC):
    """Abstract interface for the System Under Test (SUT) agent."""

    @property
    @abstractmethod
    def version(self) -> str:
        """The version identifier of the agent under test."""
        pass

    @abstractmethod
    async def run(self, input_query: str) -> Trajectory:
        """Executes the agent SUT on the input query and returns the execution trajectory."""
        pass
