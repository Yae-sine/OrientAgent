"""
OrientAgent - API Tests

Tests for the FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from api.main import app
from api.routers import session as session_router


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check_returns_ok(self, client):
        """Test that health endpoint returns successfully."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "services" in data

    def test_root_endpoint(self, client):
        """Test that root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "OrientAgent API"
        assert "endpoints" in data


class TestSessionEndpoints:
    @pytest.fixture
    def valid_session_request(self):
        """Create a valid session request body."""
        return {
            "nom": "Test Student",
            "serie_bac": "Sciences",
            "notes": {
                "maths": 16.0,
                "physique": 15.0,
                "svt": 14.0,
                "francais": 13.0,
                "arabe": 14.0,
            },
            "interets": ["informatique", "robotique"],
            "ville": "Casablanca",
            "langue": "fr",
            "budget": "public",
        }

    def test_start_session_validates_input(self, client):
        """Test that invalid input is rejected."""
        invalid_request = {
            "nom": "",  # Empty name
            "serie_bac": "InvalidSerie",
        }

        response = client.post("/api/session/start", json=invalid_request)
        assert response.status_code == 422  # Validation error

    def test_start_session_rejects_invalid_serie_bac(self, client, valid_session_request):
        """Test that invalid serie_bac is rejected."""
        valid_session_request["serie_bac"] = "Arts"

        response = client.post("/api/session/start", json=valid_session_request)
        assert response.status_code == 422

    def test_start_session_rejects_out_of_range_notes(self, client, valid_session_request):
        """Test that notes outside 0-20 range are rejected."""
        valid_session_request["notes"]["maths"] = 25.0  # Invalid

        response = client.post("/api/session/start", json=valid_session_request)
        assert response.status_code == 422

    def test_start_session_rejects_invalid_langue(self, client, valid_session_request):
        """Test that invalid langue is rejected."""
        valid_session_request["langue"] = "es"  # Not in allowed list

        response = client.post("/api/session/start", json=valid_session_request)
        assert response.status_code == 422

    def test_start_session_rejects_invalid_budget(self, client, valid_session_request):
        """Test that invalid budget is rejected."""
        valid_session_request["budget"] = "unlimited"

        response = client.post("/api/session/start", json=valid_session_request)
        assert response.status_code == 422

    def test_get_nonexistent_session_returns_404(self, client):
        """Test that fetching a non-existent session returns 404."""
        response = client.get("/api/session/nonexistent123/result")
        assert response.status_code == 404


class TestSessionBackgroundRunner:
    @pytest.mark.asyncio
    async def test_run_graph_background_persists_full_state_updates(self):
        """Ensure full node outputs are persisted, not only SSE summary data."""
        session_id = "session123"
        initial_state = {
            "session_id": session_id,
            "filieres_retrieved": [],
            "top_3": [],
            "pdf_path": None,
            "error": None,
        }

        session_router._sessions[session_id] = {
            "state": dict(initial_state),
            "status": "started",
            "events": [],
        }

        async def fake_stream_graph(_state):
            yield (
                "agent_done",
                {
                    "agent": "explorateur",
                    "data": {"filieres_count": 1},
                    "state_update": {
                        "filieres_retrieved": [{"id": "ensa_test", "nom": "ENSA Test"}],
                        "current_step": "conseiller",
                    },
                },
            )
            yield (
                "agent_done",
                {
                    "agent": "conseiller",
                    "data": {"top_3_names": ["ENSA Test"]},
                    "state_update": {
                        "top_3": [{"filiere_id": "ensa_test", "filiere_nom": "ENSA Test"}],
                        "current_step": "coach_entretien",
                    },
                },
            )
            yield (
                "agent_done",
                {
                    "agent": "pdf_generator",
                    "data": {"pdf_path": "/tmp/fake.pdf"},
                    "state_update": {
                        "pdf_path": "/tmp/fake.pdf",
                        "current_step": "complete",
                    },
                },
            )
            yield ("complete", {"session_id": session_id})

        try:
            with patch("api.routers.session.stream_graph", side_effect=fake_stream_graph), patch(
                "api.routers.session._save_session"
            ) as save_mock:
                await session_router._run_graph_background(session_id, initial_state)

            final_session = session_router._sessions[session_id]
            final_state = final_session["state"]

            assert final_session["status"] == "complete"
            assert len(final_state["filieres_retrieved"]) == 1
            assert len(final_state["top_3"]) == 1
            assert final_state["pdf_path"] == "/tmp/fake.pdf"
            save_mock.assert_called_once()
        finally:
            session_router._sessions.pop(session_id, None)

    @pytest.mark.asyncio
    async def test_run_graph_background_keeps_error_status_on_complete(self):
        """If a node outputs an error, final status must remain error."""
        session_id = "session_error"
        initial_state = {
            "session_id": session_id,
            "error": None,
        }

        session_router._sessions[session_id] = {
            "state": dict(initial_state),
            "status": "started",
            "events": [],
        }

        async def fake_stream_graph(_state):
            yield (
                "agent_done",
                {
                    "agent": "explorateur",
                    "data": {},
                    "state_update": {
                        "current_step": "error",
                        "error": "Explorateur agent failed: '_type'",
                        "filieres_retrieved": [],
                    },
                },
            )
            yield ("complete", {"session_id": session_id})

        try:
            with patch("api.routers.session.stream_graph", side_effect=fake_stream_graph), patch(
                "api.routers.session._save_session"
            ):
                await session_router._run_graph_background(session_id, initial_state)

            final_session = session_router._sessions[session_id]
            assert final_session["status"] == "error"
            assert "_type" in final_session.get("error", "")
            assert "_type" in final_session["state"].get("error", "")
        finally:
            session_router._sessions.pop(session_id, None)


class TestSchemaValidation:
    """Test Pydantic schema validation."""

    def test_session_request_schema_valid(self):
        """Test that valid data passes schema validation."""
        from api.schemas import SessionRequest

        data = SessionRequest(
            nom="Ahmed",
            serie_bac="Sciences",
            notes={"maths": 16.0, "physique": 15.0},
            interets=["informatique"],
            ville="Casablanca",
            langue="fr",
            budget="public",
        )

        assert data.nom == "Ahmed"
        assert data.serie_bac == "Sciences"

    def test_session_request_validates_serie_bac(self):
        """Test that invalid serie_bac raises validation error."""
        from api.schemas import SessionRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SessionRequest(
                nom="Ahmed",
                serie_bac="InvalidSerie",
                notes={"maths": 16.0},
                interets=["info"],
                ville="Casablanca",
            )

    def test_session_request_validates_notes_range(self):
        """Test that out-of-range notes raise validation error."""
        from api.schemas import SessionRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SessionRequest(
                nom="Ahmed",
                serie_bac="Sciences",
                notes={"maths": 25.0},  # Invalid: > 20
                interets=["info"],
                ville="Casablanca",
            )

    def test_interview_answer_request_validation(self):
        """Test InterviewAnswerRequest validation."""
        from api.schemas import InterviewAnswerRequest
        from pydantic import ValidationError

        # Valid request
        req = InterviewAnswerRequest(
            question_index=0,
            answer="This is a valid answer with more than 10 characters."
        )
        assert req.question_index == 0

        # Invalid: answer too short
        with pytest.raises(ValidationError):
            InterviewAnswerRequest(
                question_index=0,
                answer="Short"  # < 10 chars
            )

        # Invalid: negative question index
        with pytest.raises(ValidationError):
            InterviewAnswerRequest(
                question_index=-1,
                answer="This is a valid answer."
            )


class TestSSEHelper:
    """Test SSE formatting utilities."""

    def test_sse_message_encoding(self):
        """Test that SSE messages are correctly encoded."""
        from api.sse import SSEMessage

        msg = SSEMessage(
            data={"agent": "profileur", "status": "done"},
            event="agent_done"
        )

        encoded = msg.encode()

        assert "event: agent_done" in encoded
        assert "data:" in encoded
        assert "profileur" in encoded
        assert encoded.endswith("\n\n")

    def test_sse_message_with_multiline_data(self):
        """Test SSE message with multiline data."""
        from api.sse import SSEMessage

        msg = SSEMessage(data="Line 1\nLine 2\nLine 3")
        encoded = msg.encode()

        # Each line should be prefixed with "data: "
        lines = encoded.strip().split("\n")
        data_lines = [l for l in lines if l.startswith("data: ")]
        assert len(data_lines) == 3

    def test_format_agent_event(self):
        """Test agent event formatting."""
        from api.sse import format_agent_event

        event_type, event_data = format_agent_event(
            event_type="agent_start",
            agent="explorateur",
            message="Searching filières...",
            data={"count": 10}
        )

        assert event_type == "agent_start"
        assert event_data["agent"] == "explorateur"
        assert event_data["message"] == "Searching filières..."
        assert event_data["data"]["count"] == 10
