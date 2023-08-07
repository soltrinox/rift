from rift.agents import Agent
import rift.llm.openai_types as openai
import asyncio
import logging
from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Type

import rift.lsp.types as lsp
from pydantic import BaseModel
from rift.agents.agenttask import AgentTask
from rift.llm.openai_types import Message as ChatMessage
from rift.lsp import LspServer as BaseLspServer

logger = logging.getLogger(__name__)


@dataclass
class AgentRegistryItem:
    """
    Stored in the registry by the @agent decorator, created upon Rift initialization.
    """

    agent: Type[Agent]
    agent_description: str
    display_name: Optional[str] = None
    agent_icon: Optional[str] = None

    def __post_init__(self):
        if self.display_name is None:
            self.display_name = self.agent.agent_type


@dataclass
class AgentRegistryResult:
    """
    To be returned as part of a list of available agent workflows to the language server client.
    """

    agent_type: str
    agent_description: str
    display_name: Optional[str] = None
    agent_icon: Optional[str] = None  # svg icon information


@dataclass
class AgentRegistry:
    """
    AgentRegistry is an organizational class that is used to track all agents in one central location.
    """

    # Initial registry to store agents
    registry: Dict[str, AgentRegistryItem] = field(default_factory=dict)

    def __getitem__(self, key):
        return self.get_agent(key)

    def register_agent(
        self,
        agent: Type[Agent],
        agent_description: str,
        display_name: Optional[str] = None,
        agent_icon: Optional[str] = None,
    ) -> None:
        if agent.agent_type in self.registry:
            raise ValueError(f"Agent '{agent.agent_type}' is already registered.")
        self.registry[agent.agent_type] = AgentRegistryItem(
            agent=agent,
            agent_description=agent_description,
            display_name=display_name,
            agent_icon=agent_icon,
        )

    def get_agent(self, agent_type: str) -> Type[Agent]:
        result: AgentRegistryItem | None = self.registry.get(agent_type)
        if result is not None:
            return result.agent
        else:
            raise ValueError(f"Agent not found: {agent_type}")

    def get_agent_icon(self, item: AgentRegistryItem) -> ...:
        return None  # TODO

    def list_agents(self) -> List[AgentRegistryResult]:
        return [
            AgentRegistryResult(
                agent_type=item.agent.agent_type,
                agent_description=item.agent_description,
                agent_icon=item.agent_icon,
                display_name=item.display_name,
            )
            for item in self.registry.values()
        ]    


AGENT_REGISTRY = AgentRegistry()  # Creating an instance of AgentRegistry

def agent(
    agent_description: str, display_name: Optional[str] = None, agent_icon: Optional[str] = None
):
    def decorator(cls: Type[Agent]) -> Type[Agent]:
        AGENT_REGISTRY.register_agent(
            cls, agent_description, display_name, agent_icon
        )  # Registering the agent
        return cls

    return decorator
