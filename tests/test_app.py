import os
import sys
from unittest.mock import patch, MagicMock

import pytest

# --- Make sure the project root (where app.py lives) is on sys.path ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Telling ruff lint to ignore that this import isn't at the top, it can't be!
import app as weather_app  # # noqa: E402

@pytest.fixture
def client(monkeypatch):
    """
    Provide a Flask test client for the app.

    Also monkeypatch API_KEY so the URL we assert in tests is deterministic.
    """
    monkeypatch.setattr(weather_app, "API_KEY", "test-api-key")
    weather_app.app.config["TESTING"] = True
    return weather_app.app.test_client()


def test_get_index_shows_form(client):
    """
    A GET on "/" should:
    - return HTTP 200
    - show the form text from index.html
    """
    response = client.get("/")

    assert response.status_code == 200
    assert b"Check the Weather" in response.data
    assert b"Enter city" in response.data


@patch("app.requests.get")
def test_post_valid_city_shows_weather(mock_get, client):
    """
    When posting a valid city:
    - the app should call the OpenWeather API (mocked)
    - the page should show the weather info for that city
    """

    # Fake API response shaped like OpenWeather JSON
    fake_api_response = {
        "name": "London",
        "main": {"temp": 72.0},
        "weather": [{"description": "light rain"}],
        "wind": {"speed": 5.5},
    }

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = fake_api_response
    mock_get.return_value = mock_response

    response = client.post("/", data={"city": "london"})

    assert response.status_code == 200

    # Ensure we actually called requests.get once
    assert mock_get.call_count == 1

    # Check the URL we called contains the right pieces
    called_url = mock_get.call_args[0][0]
    assert "q=london" in called_url
    assert "units=imperial" in called_url
    assert "appid=test-api-key" in called_url

    # Check rendered HTML contains key bits of the fake data
    # Note: your template title-cases city and description
    assert b"Weather in London" in response.data
    assert b"72.0" in response.data  # Temperature
    assert b"Light Rain" in response.data  # Condition (title-cased)
    assert b"5.5" in response.data  # Wind speed


@patch("app.requests.get")
def test_post_invalid_city_shows_error(mock_get, client):
    """
    When the API call fails (response.ok == False):
    - the app should render the error message "City not found"
    """

    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.json.return_value = {"message": "city not found"}
    mock_get.return_value = mock_response

    response = client.post("/", data={"city": "nosuchcity"})

    assert response.status_code == 200

    # You set weather_data = {'error': 'City not found'}
    # and index.html uses {{ weather.error }}.
    assert b"City not found" in response.data

    # Make sure the normal "Weather in ..." header is NOT present
    assert b"Weather in" not in response.data
