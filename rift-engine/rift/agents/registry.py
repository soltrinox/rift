from typing import Dict
from abstract import Agent

class AgentRegistry:
    def __init__(self):
        self.registry: Dict[int, Agent] = {}

    def register_agent(self, agent: Agent):
        if agent.id in self.registry:
            raise ValueError(f"Agent with ID {agent.id} is already registered.")
        self.registry[agent.id] = agent

    def get_agent(self, id: int):
        return self.registry.get(id)

    def list_agents(self):
        return list(self.registry.values())

    def delete_agent(self, id: int):
        if id in self.registry:
            del self.registry[id]
        else:
            raise ValueError(f"No agent found with ID {id}.")
