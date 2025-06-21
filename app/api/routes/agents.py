from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from ...store.game_store import game_store
from ...models.game_models import ActionType

router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.get("/")
async def get_agents() -> List[Dict[str, Any]]:
    """Get all available agents"""
    agents = game_store.get_all_agents()
    return [agent.model_dump() for agent in agents]


@router.get("/action-types")
async def get_action_types() -> Dict[str, Any]:
    """Get all available action types"""
    return {
        "action_types": [action.value for action in ActionType],
        "descriptions": {
            "fold": "Give up the hand",
            "check": "Pass the action without betting",
            "call": "Match the current bet",
            "raise": "Increase the current bet",
            "all_in": "Bet all remaining chips",
        },
    }


@router.get("/{agent_id}")
async def get_agent(agent_id: str) -> Dict[str, Any]:
    """Get agent details by ID"""
    agent = game_store.get_agent_personality(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get agent stats
    stats = game_store.get_agent_stats(agent_id)

    return {"agent": agent.model_dump(), "stats": stats.model_dump() if stats else None}


@router.get("/{agent_id}/stats")
async def get_agent_stats(agent_id: str) -> Dict[str, Any]:
    """Get agent statistics"""
    stats = game_store.get_agent_stats(agent_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Agent stats not found")

    return dict(stats.model_dump())


@router.get("/{agent_id}/memories")
async def get_agent_memories(agent_id: str, limit: int = 10) -> Dict[str, Any]:
    """Get agent memories"""
    memories = game_store.get_agent_memories(agent_id)

    # Limit the number of memories returned
    recent_memories = memories[-limit:] if memories else []

    return {
        "agent_id": agent_id,
        "total_memories": len(memories),
        "memories": [memory.model_dump() for memory in recent_memories],
    }


@router.get("/{agent_id}/performance")
async def get_agent_performance(agent_id: str) -> Dict[str, Any]:
    """Get agent performance metrics"""
    performance = game_store.get_agent_performance(agent_id)
    if not performance:
        raise HTTPException(status_code=404, detail="Agent performance data not found")

    return dict(performance)
