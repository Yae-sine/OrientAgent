"""
OrientAgent - API Pydantic Schemas

Request and response models for the FastAPI endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SessionRequest(BaseModel):
    """Request body for POST /api/session/start"""
    
    nom: str = Field(..., min_length=1, max_length=100, description="Nom de l'étudiant")
    serie_bac: str = Field(..., description="Série du Baccalauréat")
    notes: dict[str, float] = Field(..., description="Notes par matière (ex: {'maths': 16.5})")
    interets: list[str] = Field(..., min_length=1, description="Centres d'intérêt")
    ville: str = Field(..., min_length=1, description="Ville préférée pour les études")
    langue: str = Field(default="fr", description="Langue préférée (fr, ar, en)")
    budget: str = Field(default="public", description="Budget (public, prive_abordable, prive_premium)")
    
    @field_validator("serie_bac")
    @classmethod
    def validate_serie_bac(cls, v: str) -> str:
        valid_series = ["Sciences", "Lettres", "Economie", "Technique"]
        if v not in valid_series:
            raise ValueError(f"serie_bac must be one of: {valid_series}")
        return v
    
    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: dict) -> dict:
        for subject, note in v.items():
            if not isinstance(note, (int, float)):
                raise ValueError(f"Note for {subject} must be a number")
            if not 0 <= note <= 20:
                raise ValueError(f"Note for {subject} must be between 0 and 20")
        return v
    
    @field_validator("langue")
    @classmethod
    def validate_langue(cls, v: str) -> str:
        valid_langues = ["fr", "ar", "en"]
        if v not in valid_langues:
            raise ValueError(f"langue must be one of: {valid_langues}")
        return v
    
    @field_validator("budget")
    @classmethod
    def validate_budget(cls, v: str) -> str:
        valid_budgets = ["public", "prive_abordable", "prive_premium"]
        if v not in valid_budgets:
            raise ValueError(f"budget must be one of: {valid_budgets}")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "nom": "Ahmed Benali",
                    "serie_bac": "Sciences",
                    "notes": {
                        "maths": 16.5,
                        "physique": 15.0,
                        "svt": 14.0,
                        "francais": 13.5,
                        "arabe": 14.0
                    },
                    "interets": ["informatique", "robotique", "intelligence artificielle"],
                    "ville": "Casablanca",
                    "langue": "fr",
                    "budget": "public"
                }
            ]
        }
    }


class SessionResponse(BaseModel):
    """Response for POST /api/session/start"""
    
    session_id: str = Field(..., description="Unique session identifier")
    status: str = Field(..., description="Session status (started, running, complete, error)")
    message: str = Field(default="", description="Additional status message")


class AgentEvent(BaseModel):
    """SSE event format for agent progress"""
    
    event: str = Field(..., description="Event type (agent_start, agent_done, error, complete)")
    agent: Optional[str] = Field(None, description="Agent name if applicable")
    message: Optional[str] = Field(None, description="Human-readable message")
    data: Optional[dict] = Field(None, description="Event-specific data")


class InterviewAnswerRequest(BaseModel):
    """Request body for submitting an interview answer"""
    
    question_index: int = Field(..., ge=0, lt=10, description="Index of the question being answered")
    answer: str = Field(..., min_length=10, max_length=2000, description="Student's answer")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question_index": 0,
                    "answer": "J'ai choisi cette filière car je suis passionné par l'informatique depuis mon enfance. Je programme depuis l'âge de 14 ans et j'ai réalisé plusieurs projets personnels en Python et JavaScript."
                }
            ]
        }
    }


class InterviewEvaluation(BaseModel):
    """Response for interview answer evaluation"""
    
    clarte: int = Field(..., ge=0, le=10, description="Clarity score (0-10)")
    motivation: int = Field(..., ge=0, le=10, description="Motivation score (0-10)")
    connaissance: int = Field(..., ge=0, le=10, description="Knowledge score (0-10)")
    feedback: str = Field(..., description="Constructive feedback")
    question_index: int = Field(..., description="Index of the evaluated question")
    is_complete: bool = Field(default=False, description="Whether the interview is complete")


class FiliereSelection(BaseModel):
    """Request body for selecting a filière for interview"""
    
    filiere_id: str = Field(..., description="ID of the selected filière from top 3")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "filiere_id": "ensa_casablanca_genie_info"
                }
            ]
        }
    }


class SessionResult(BaseModel):
    """Full session result response"""
    
    session_id: str
    status: str
    nom: str
    serie_bac: str
    domain_scores: dict[str, float]
    learning_style: str
    filieres_count: int
    top_3: list[dict]
    filiere_choisie: Optional[str] = None
    interview_score: Optional[int] = None
    interview_feedback: Optional[dict] = None
    pdf_path: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = Field(default="healthy")
    version: str = Field(default="1.0.0")
    services: dict[str, str] = Field(default_factory=dict)
