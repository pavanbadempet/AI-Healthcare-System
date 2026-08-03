"""
AI Healthcare System — Agentic AI Reflective Memory Store.

Provides episodic and semantic memory for autonomous agents, enabling
reflection on past decisions, self-correction, and long-term learning.
"""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    """A single episodic memory entry."""
    episode_id: str
    agent_name: str
    action_taken: str
    outcome: str
    reward_signal: float = 0.0
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReflectionInsight(BaseModel):
    """An insight derived from reflecting on past episodes."""
    insight: str
    source_episodes: List[str]
    confidence: float


class AgentReflectiveMemory:
    """
    Episodic memory store with reflection capability.

    Agents write experiences after each action, then periodically
    reflect to extract reusable insights that improve future decisions.
    """

    def __init__(self, max_episodes: int = 1000) -> None:
        self.episodes: List[MemoryEntry] = []
        self.insights: List[ReflectionInsight] = []
        self.max_episodes = max_episodes

    def record_episode(
        self,
        episode_id: str,
        agent_name: str,
        action_taken: str,
        outcome: str,
        reward_signal: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryEntry:
        """Record an episode after an agent action."""
        entry = MemoryEntry(
            episode_id=episode_id,
            agent_name=agent_name,
            action_taken=action_taken,
            outcome=outcome,
            reward_signal=reward_signal,
            metadata=metadata or {},
        )
        self.episodes.append(entry)
        if len(self.episodes) > self.max_episodes:
            self.episodes.pop(0)
        return entry

    def recall(self, agent_name: Optional[str] = None, limit: int = 10) -> List[MemoryEntry]:
        """Recall recent episodes, optionally filtered by agent."""
        filtered = self.episodes if agent_name is None else [e for e in self.episodes if e.agent_name == agent_name]
        return filtered[-limit:]

    def reflect(self) -> List[ReflectionInsight]:
        """
        Reflect on stored episodes to extract reusable insights.

        Uses reward signals to identify successful and failed action patterns.
        """
        if len(self.episodes) < 2:
            return self.insights

        successful = [e for e in self.episodes if e.reward_signal > 0.5]
        failed = [e for e in self.episodes if e.reward_signal < -0.5]

        if successful:
            self.insights.append(ReflectionInsight(
                insight=f"Repeated success pattern: actions like '{successful[-1].action_taken}' yield positive outcomes.",
                source_episodes=[e.episode_id for e in successful[-3:]],
                confidence=min(0.95, 0.5 + 0.1 * len(successful)),
            ))

        if failed:
            self.insights.append(ReflectionInsight(
                insight=f"Failure pattern detected: actions like '{failed[-1].action_taken}' should be avoided or modified.",
                source_episodes=[e.episode_id for e in failed[-3:]],
                confidence=min(0.90, 0.4 + 0.1 * len(failed)),
            ))

        return self.insights


# Global singleton
agent_reflective_memory = AgentReflectiveMemory()
