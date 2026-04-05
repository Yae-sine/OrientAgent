"""
OrientAgent - RAG Pipeline Tests

Tests for the RAG indexer and retriever.
"""

import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from rag.indexer import (
    filiere_to_document,
    validate_card,
    load_corpus,
    REQUIRED_FIELDS,
)


# Test fixtures
@pytest.fixture
def valid_filiere_card() -> dict:
    """Create a valid filière card for testing."""
    return {
        "id": "test_filiere_001",
        "nom": "Test Filière — Génie Test",
        "type": "ENSA",
        "ville": "Casablanca",
        "domaine": "tech",
        "serie_bac_requise": ["Sciences", "Technique"],
        "langue_enseignement": "fr",
        "conditions_acces": "Concours national, mention recommandée",
        "duree_annees": 5,
        "frais_annuels_mad": 0,
        "taux_emploi": 90,
        "salaire_moyen_premier_emploi_mad": 8000,
        "debouches": ["Ingénieur", "Consultant", "Chef de projet"],
        "grandes_ecoles_accessibles": ["EMI", "ENSIAS"],
        "description": "Formation d'excellence en génie test.",
    }


@pytest.fixture
def invalid_filiere_card() -> dict:
    """Create an invalid filière card (missing fields)."""
    return {
        "id": "incomplete_card",
        "nom": "Incomplete Card",
        # Missing many required fields
    }


# filiere_to_document Tests
class TestFiliereToDocument:
    def test_creates_searchable_document(self, valid_filiere_card):
        """Test that filiere_to_document creates a comprehensive document string."""
        doc = filiere_to_document(valid_filiere_card)

        # Check that key information is included
        assert "Test Filière — Génie Test" in doc
        assert "ENSA" in doc
        assert "Casablanca" in doc
        assert "tech" in doc
        assert "Sciences" in doc
        assert "90%" in doc
        assert "Ingénieur" in doc
        assert "Formation d'excellence" in doc

    def test_handles_empty_lists(self):
        """Test handling of cards with empty lists."""
        card = {
            "id": "empty_lists",
            "nom": "Empty Lists Filière",
            "type": "Test",
            "ville": "Test",
            "domaine": "tech",
            "serie_bac_requise": [],
            "langue_enseignement": "fr",
            "conditions_acces": "Test",
            "duree_annees": 3,
            "frais_annuels_mad": 0,
            "taux_emploi": 80,
            "salaire_moyen_premier_emploi_mad": 5000,
            "debouches": [],
            "description": "Test description",
        }

        doc = filiere_to_document(card)
        assert "Empty Lists Filière" in doc

    def test_handles_missing_optional_fields(self, valid_filiere_card):
        """Test handling of cards without optional grandes_ecoles_accessibles."""
        del valid_filiere_card["grandes_ecoles_accessibles"]
        doc = filiere_to_document(valid_filiere_card)

        # Should still create a valid document
        assert "Test Filière" in doc
        assert "Grandes écoles accessibles" not in doc


# validate_card Tests
class TestValidateCard:
    def test_valid_card_returns_no_errors(self, valid_filiere_card):
        """Test that a valid card passes validation."""
        errors = validate_card(valid_filiere_card, "test.json")
        assert len(errors) == 0

    def test_missing_required_fields(self, invalid_filiere_card):
        """Test that missing fields are reported."""
        errors = validate_card(invalid_filiere_card, "test.json")

        # Should have errors for missing fields
        assert len(errors) > 0
        assert any("type" in e for e in errors)

    def test_invalid_domaine(self, valid_filiere_card):
        """Test that invalid domaine values are caught."""
        valid_filiere_card["domaine"] = "invalid_domain"
        errors = validate_card(valid_filiere_card, "test.json")

        assert any("domaine" in e.lower() for e in errors)

    def test_invalid_taux_emploi(self, valid_filiere_card):
        """Test that out-of-range taux_emploi is caught."""
        valid_filiere_card["taux_emploi"] = 150
        errors = validate_card(valid_filiere_card, "test.json")

        assert any("taux_emploi" in e for e in errors)

    def test_serie_bac_must_be_list(self, valid_filiere_card):
        """Test that serie_bac_requise must be a list."""
        valid_filiere_card["serie_bac_requise"] = "Sciences"
        errors = validate_card(valid_filiere_card, "test.json")

        assert any("serie_bac_requise" in e for e in errors)


# Corpus Loading Tests
class TestCorpusLoading:
    def test_load_corpus_from_valid_directory(self, valid_filiere_card):
        """Test loading corpus from a directory with valid JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test JSON file
            test_file = Path(tmpdir) / "test_filieres.json"
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump([valid_filiere_card], f)

            # Patch CORPUS_PATH
            with patch("rag.indexer.CORPUS_PATH", Path(tmpdir)):
                cards, errors = load_corpus()

            assert len(cards) == 1
            assert cards[0]["id"] == "test_filiere_001"
            assert len(errors) == 0

    def test_load_corpus_reports_invalid_cards(self, valid_filiere_card, invalid_filiere_card):
        """Test that invalid cards are reported but valid ones are still loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "mixed.json"
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump([valid_filiere_card, invalid_filiere_card], f)

            with patch("rag.indexer.CORPUS_PATH", Path(tmpdir)):
                cards, errors = load_corpus()

            # Valid card should be loaded
            assert len(cards) == 1
            # Invalid card should generate errors
            assert len(errors) > 0


# Corpus File Validation Tests
class TestCorpusFiles:
    """Test that all actual corpus files are valid."""

    CORPUS_DIR = Path(__file__).parent.parent / "rag" / "corpus"

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "rag" / "corpus").exists(),
        reason="Corpus directory not found"
    )
    def test_all_corpus_files_are_valid_json(self):
        """Test that all JSON files in corpus/ are valid JSON."""
        for json_file in self.CORPUS_DIR.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    assert isinstance(data, list), f"{json_file.name} should contain a JSON array"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {json_file.name}: {e}")

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "rag" / "corpus").exists(),
        reason="Corpus directory not found"
    )
    def test_all_corpus_cards_have_required_fields(self):
        """Test that all cards in corpus have required fields."""
        all_errors = []

        for json_file in self.CORPUS_DIR.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                cards = json.load(f)

            for card in cards:
                errors = validate_card(card, json_file.name)
                all_errors.extend(errors)

        if all_errors:
            error_msg = "\n".join(all_errors[:10])  # Show first 10 errors
            if len(all_errors) > 10:
                error_msg += f"\n... and {len(all_errors) - 10} more errors"
            pytest.fail(f"Corpus validation errors:\n{error_msg}")

    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "rag" / "corpus").exists(),
        reason="Corpus directory not found"
    )
    def test_corpus_has_diverse_filieres(self):
        """Test that corpus covers multiple types and domains."""
        types_found = set()
        domains_found = set()
        villes_found = set()

        for json_file in self.CORPUS_DIR.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                cards = json.load(f)

            for card in cards:
                if "type" in card:
                    types_found.add(card["type"])
                if "domaine" in card:
                    domains_found.add(card["domaine"])
                if "ville" in card:
                    villes_found.add(card["ville"])

        # Should have diverse coverage
        assert len(types_found) >= 3, f"Need more filière types, found: {types_found}"
        assert len(domains_found) >= 2, f"Need more domains, found: {domains_found}"
        assert len(villes_found) >= 3, f"Need more cities, found: {villes_found}"


# ChromaDB Retriever Tests (with mocking)
class TestChromaDBRetriever:
    def test_retriever_raises_on_uninitialized_db(self):
        """Test that retriever raises clear error when DB not initialized."""
        from rag.retriever import chromadb_retrieve, reset_cache

        # Reset any cached state
        reset_cache()

        # Use a non-existent path
        with patch.dict(os.environ, {"CHROMA_DB_PATH": "/nonexistent/path"}):
            with patch("rag.retriever.CHROMA_DB_PATH", "/nonexistent/path"):
                reset_cache()
                with pytest.raises(RuntimeError) as excinfo:
                    chromadb_retrieve("test query")

                assert "not initialized" in str(excinfo.value).lower()

    def test_retriever_formats_results_correctly(self):
        """Test that retriever adds similarity_score and formats results."""
        from rag.retriever import chromadb_retrieve, reset_cache

        # Create mock collection
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["Doc 1", "Doc 2"]],
            "metadatas": [[
                {"nom": "Filière 1", "type": "ENSA", "ville": "Casa"},
                {"nom": "Filière 2", "type": "FST", "ville": "Rabat"},
            ]],
            "distances": [[0.5, 0.8]],
        }

        # Mock the ChromaDB client
        with patch("rag.retriever._get_chroma_collection", return_value=mock_collection):
            with patch("rag.retriever._get_embedding_model") as mock_model:
                mock_model.return_value.encode.return_value = MagicMock(tolist=lambda: [0.1] * 384)

                results = chromadb_retrieve("test query", k=2)

        assert len(results) == 2
        assert "similarity_score" in results[0]
        assert results[0]["id"] == "id1"
        assert results[0]["nom"] == "Filière 1"
