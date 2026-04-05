"""
OrientAgent - SSE Helper

Server-Sent Events helper for streaming agent progress to the frontend.
"""

import json
import asyncio
from typing import AsyncGenerator, Any


class SSEMessage:
    """Represents a Server-Sent Event message."""
    
    def __init__(
        self,
        data: Any,
        event: str | None = None,
        id: str | None = None,
        retry: int | None = None
    ):
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry
    
    def encode(self) -> str:
        """Encode the message as SSE format."""
        lines = []
        
        if self.id is not None:
            lines.append(f"id: {self.id}")
        
        if self.event is not None:
            lines.append(f"event: {self.event}")
        
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
        
        # Handle data serialization
        if isinstance(self.data, dict):
            data_str = json.dumps(self.data, ensure_ascii=False)
        else:
            data_str = str(self.data)
        
        # SSE data can be multiline, each line prefixed with "data: "
        for line in data_str.split("\n"):
            lines.append(f"data: {line}")
        
        # End with double newline
        return "\n".join(lines) + "\n\n"


async def event_stream(
    event_generator: AsyncGenerator[tuple[str, dict], None],
    heartbeat_interval: float = 15.0
) -> AsyncGenerator[str, None]:
    """
    Convert an async generator of events to SSE format with heartbeat.
    
    Args:
        event_generator: Async generator yielding (event_type, data) tuples
        heartbeat_interval: Seconds between heartbeat messages
    
    Yields:
        SSE-formatted strings
    """
    last_event_time = asyncio.get_event_loop().time()
    event_iter = event_generator.__aiter__()
    
    while True:
        try:
            # Wait for next event or heartbeat timeout
            event = await asyncio.wait_for(
                event_iter.__anext__(),
                timeout=heartbeat_interval
            )
            
            event_type, data = event
            message = SSEMessage(data=data, event=event_type)
            yield message.encode()
            
            last_event_time = asyncio.get_event_loop().time()
            
        except asyncio.TimeoutError:
            # Send heartbeat
            heartbeat = SSEMessage(data={"type": "heartbeat"}, event="heartbeat")
            yield heartbeat.encode()
            
        except StopAsyncIteration:
            # Generator exhausted
            break
        except Exception as e:
            # Send error event
            error_msg = SSEMessage(
                data={"error": str(e)},
                event="error"
            )
            yield error_msg.encode()
            break


def format_agent_event(event_type: str, agent: str, message: str = "", data: dict = None) -> tuple[str, dict]:
    """
    Format an agent event for SSE streaming.
    
    Args:
        event_type: One of "agent_start", "agent_done", "error", "complete"
        agent: Agent name (profileur, explorateur, conseiller, coach_entretien)
        message: Human-readable status message
        data: Additional event data
    
    Returns:
        Tuple of (event_type, event_data) for SSE
    """
    event_data = {
        "agent": agent,
        "message": message or _get_default_message(event_type, agent),
    }
    
    if data:
        event_data["data"] = data
    
    return (event_type, event_data)


def _get_default_message(event_type: str, agent: str) -> str:
    """Get default message for an event type and agent."""
    agent_names = {
        "profileur": "Profileur",
        "explorateur": "Explorateur",
        "conseiller": "Conseiller",
        "coach_entretien": "Coach Entretien",
        "pdf_generator": "Générateur PDF",
    }
    
    agent_display = agent_names.get(agent, agent.title())
    
    if event_type == "agent_start":
        messages = {
            "profileur": "Analyse de ton profil en cours...",
            "explorateur": "Recherche des filières adaptées...",
            "conseiller": "Préparation des recommandations...",
            "coach_entretien": "Génération des questions d'entretien...",
            "pdf_generator": "Création du rapport PDF...",
        }
        return messages.get(agent, f"Démarrage de {agent_display}...")
    
    elif event_type == "agent_done":
        messages = {
            "profileur": "Profil analysé ✓",
            "explorateur": "Filières identifiées ✓",
            "conseiller": "Recommandations prêtes ✓",
            "coach_entretien": "Questions préparées ✓",
            "pdf_generator": "Rapport PDF créé ✓",
        }
        return messages.get(agent, f"{agent_display} terminé ✓")
    
    elif event_type == "error":
        return f"Erreur dans {agent_display}"
    
    elif event_type == "complete":
        return "Analyse complète ! Consultez vos résultats."
    
    return ""


async def send_progress_events(session_id: str, step: str, progress: int) -> tuple[str, dict]:
    """
    Send a progress update event.
    
    Args:
        session_id: Current session ID
        step: Current step name
        progress: Progress percentage (0-100)
    
    Returns:
        SSE event tuple
    """
    return ("progress", {
        "session_id": session_id,
        "step": step,
        "progress": progress,
    })
