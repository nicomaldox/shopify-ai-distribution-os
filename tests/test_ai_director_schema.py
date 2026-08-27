import pytest
from pydantic import ValidationError
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/apps/core-api")))
from services.schemas import DirectorSpec

def test_director_spec_valid():
    """Test that valid input passes validation."""
    data = {
        "visual_hook": "A vibrant split screen showing the product.",
        "narration_text": "This is the best thing ever! #Ad",
        "pacing_notes": ["Fast cut here"],
        "ad_disclosures": ["#Ad"]
    }
    spec = DirectorSpec(**data)
    assert spec.visual_hook == data["visual_hook"]
    assert spec.ad_disclosures == ["#Ad"]

def test_director_spec_missing_fields():
    """Test that missing fields raise ValidationError."""
    data = {
        "visual_hook": "Missing other fields."
    }
    with pytest.raises(ValidationError):
        DirectorSpec(**data)
