import pytest
from fastapi.testclient import TestClient
import os
from unittest.mock import patch, MagicMock

# Set some dummy env vars before importing app
os.environ["SECRET_KEY"] = "testsecret"
os.environ["ADMIN_EMAIL"] = "admin@test.com"
os.environ["ADMIN_PASSWORD"] = "password"

from main import app, serpapi_cache
from png_scraper.serpapi_client import SerpApiClient

client = TestClient(app)

def test_serpapi_client_query_construction():
    """Test that the SerpApiClient constructs the correct parameters."""
    api = SerpApiClient(api_key="test_key")
    # Mocking the search object
    with patch("png_scraper.serpapi_client.GoogleSearch") as mock_search:
        mock_instance = mock_search.return_value
        mock_instance.get_dict.return_value = {"local_results": [{"title": "School A", "gps_coordinates": {"latitude": -9.4, "longitude": 147.1}}]}

        results = api.fetch_places("schools")

        # Verify construction
        args, kwargs = mock_search.call_args
        params = args[0]
        assert params["engine"] == "google_maps"
        # Should now include "Port Moresby" in the query
        assert "school" in params["q"].lower()
        assert "port moresby" in params["q"].lower()
        assert params["ll"] == "@-9.4438,147.1803,13z"
        assert params["api_key"] == "test_key"

        assert len(results) == 1
        assert results[0]["name"] == "School A"

def test_heatmap_places_endpoint_caching():
    """Test that the /api/heatmap/places endpoint uses the global serpapi_cache."""
    # Clear cache
    serpapi_cache.clear()

    # We need to bypass authentication for this test
    from main import get_current_user
    app.dependency_overrides[get_current_user] = lambda: MagicMock(email="test@test.com", role="admin")

    # Patch the function in the main module where it is imported
    with patch("main.get_serpapi_places") as mock_fetch:
        mock_fetch.return_value = [{"name": "Cached Place", "lat": -9.4, "lng": 147.1}]

        # First request
        resp1 = client.get("/api/heatmap/places?category=schools")
        assert resp1.status_code == 200
        assert resp1.json()["cached"] is False
        assert mock_fetch.call_count == 1

        # Second request (should be cached)
        resp2 = client.get("/api/heatmap/places?category=schools")
        assert resp2.status_code == 200
        assert resp2.json()["cached"] is True
        assert mock_fetch.call_count == 1

    app.dependency_overrides.clear()

def test_serpapi_client_handles_error():
    """Test that the client handles API errors gracefully."""
    api = SerpApiClient(api_key="test_key")
    with patch("png_scraper.serpapi_client.GoogleSearch") as mock_search:
        mock_instance = mock_search.return_value
        mock_instance.get_dict.return_value = {"error": "Invalid API key"}

        results = api.fetch_places("invalid")
        assert results == []
