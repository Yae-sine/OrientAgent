"""
OrientAgent - Shared LangGraph State

This module defines the StudentProfile TypedDict that serves as the
shared state passed between all agents in the LangGraph pipeline.
"""

from typing import TypedDict, Annotated
import operator


class StudentProfile(TypedDict):
    """
    The shared state for the OrientAgent LangGraph pipeline.
    Each agent receives this state and returns a partial update.
    """
    
    # Input fields (from user onboarding)
    nom: str
    serie_bac: str  # "Sciences", "Lettres", "Economie", "Technique"
    notes: dict  # {"maths": 16.5, "physique": 14.0, ...}
    interets: Annotated[list[str], operator.add]  # ["informatique", "robotique", ...]
    ville: str  # "Casablanca", "Rabat", ...
    langue: str  # "fr", "ar", "en"
    budget: str  # "public", "prive_abordable", "prive_premium"
    
    # Agent 1 (Profileur) output
    domain_scores: dict  # {"sciences": 0.87, "tech": 0.72, "lettres": 0.45, "economie": 0.60}
    learning_style: str  # "theorique", "pratique", "mixte"
    constraints: dict  # {"ville": str, "langue": str, "budget": str, "mobilite": bool}
    
    # Agent 2 (Explorateur) output
    filieres_retrieved: Annotated[list[dict], operator.add]  # RAG results with metadata
    
    # Agent 3 (Conseiller) output
    top_3: Annotated[list[dict], operator.add]  # [{filiere, score, justification, plan}]
    
    # Agent 4 (Coach Entretien) output
    filiere_choisie: str
    interview_questions: Annotated[list[str], operator.add]
    interview_answers: Annotated[list[str], operator.add]
    interview_score: int
    interview_feedback: dict  # {points_forts: [], axes_amelioration: []}
    
    # Meta fields
    session_id: str
    current_step: str  # "profileur", "explorateur", "conseiller", "coach", "complete"
    pdf_path: str | None
    error: str | None  # Error message if any step fails


def create_initial_state(
    nom: str,
    serie_bac: str,
    notes: dict,
    interets: list[str],
    ville: str,
    langue: str,
    budget: str,
    session_id: str
) -> StudentProfile:
    """
    Create an initial StudentProfile state with user input.
    All agent output fields are initialized to empty/None values.
    """
    return StudentProfile(
        # Input fields
        nom=nom,
        serie_bac=serie_bac,
        notes=notes,
        interets=interets,
        ville=ville,
        langue=langue,
        budget=budget,
        
        # Agent outputs (empty initially)
        domain_scores={},
        learning_style="",
        constraints={},
        filieres_retrieved=[],
        top_3=[],
        filiere_choisie="",
        interview_questions=[],
        interview_answers=[],
        interview_score=0,
        interview_feedback={},
        
        # Meta
        session_id=session_id,
        current_step="profileur",
        pdf_path=None,
        error=None,
    )
