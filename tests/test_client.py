# tests/test_client.py
from unittest.mock import patch, MagicMock
from api.client import WPClient


def make_client():
    return WPClient("http://acf-tool-dev.local", "admin", "test_password")


def test_client_base_url_strips_slash():
    client = WPClient("http://acf-tool-dev.local/", "admin", "pass")
    assert not client.base_url.endswith("/")


def test_client_stores_credentials():
    client = WPClient("http://acf-tool-dev.local", "admin", "pass")
    assert client.auth.username == "admin"
    assert client.auth.password == "pass"


def test_test_connection_success():
    client = make_client()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"name": "admin", "id": 1}

    with patch.object(client, "get", return_value=mock_response):
        result = client.test_connection()
    assert result is True


def test_test_connection_401():
    client = make_client()
    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch.object(client, "get", return_value=mock_response):
        result = client.test_connection()
    assert result is False


def test_test_connection_404():
    client = make_client()
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch.object(client, "get", return_value=mock_response):
        result = client.test_connection()
    assert result is False


def test_get_builds_correct_url():
    client = make_client()
    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        client.get("wp/v2/posts")
        called_url = mock_get.call_args[0][0]
        assert called_url == "http://acf-tool-dev.local/wp-json/wp/v2/posts"


def test_post_builds_correct_url():
    client = make_client()
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=201)
        client.post("wp/v2/posts", {"title": "Test"})
        called_url = mock_post.call_args[0][0]
        assert called_url == "http://acf-tool-dev.local/wp-json/wp/v2/posts"