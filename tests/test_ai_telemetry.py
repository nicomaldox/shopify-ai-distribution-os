import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/apps/core-api")))
from services.ai_director import telemetry_logger_node

@pytest.mark.asyncio
async def test_telemetry_logger_node_insertion():
    """Test that the telemetry node inserts correct mock values into DB."""
    # Setup mock DB session
    mock_db = AsyncMock()
    mock_session_generator = AsyncMock()
    mock_session_generator.__aiter__.return_value = [mock_db]
    
    # State mock
    state = {
        "trace_id": "trace_test_123",
        "creator_id": "creator-test-id",
        "product_id": "prod-1",
        "product_title": "Test Prod",
        "product_price": "19.99",
        "total_tokens": 1000,
        "claims_accuracy_score": 1.0,
        "status": "SUCCESS"
    }

    with patch("services.ai_director.get_db_session", return_value=mock_session_generator):
        result = await telemetry_logger_node(state)
        
    # Verify execution
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()
    
    # Verify exact insertion parameters
    call_args = mock_db.execute.call_args[0]
    params = call_args[1]
    
    assert params["trace_id"] == "trace_test_123"
    assert params["total_tokens"] == 1000
    assert params["estimated_cost_usd"] == 0.005 # (1000 / 1000) * 0.005
    assert params["claims_accuracy_score"] == 1.0
    assert params["status"] == "SUCCESS"
    
    # Node should return an empty dict to not overwrite anything
    assert result == {}
