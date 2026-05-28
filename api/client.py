# api/client.py
import requests
from requests.auth import HTTPBasicAuth


class WPClient:
    """
    WordPress REST API client using Application Password authentication.
    All API calls go through this class.
    """

    def __init__(self, base_url, username, password):
        """
        Args:
            base_url: e.g. "http://acf-tool-dev.local"
            username: WordPress admin username
            password: Application Password (with or without spaces)
        """
        self.base_url = base_url.rstrip("/")
        self.auth     = HTTPBasicAuth(username, password)
        self.headers  = {"Content-Type": "application/json"}

    def get(self, endpoint):
        """Makes a GET request to the WP REST API."""
        url = f"{self.base_url}/wp-json/{endpoint}"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        return response

    def post(self, endpoint, data):
        """Makes a POST request to the WP REST API."""
        url = f"{self.base_url}/wp-json/{endpoint}"
        response = requests.post(
            url, auth=self.auth, headers=self.headers, json=data
        )
        return response

    def patch(self, endpoint, data):
        """Makes a PATCH request to the WP REST API."""
        url = f"{self.base_url}/wp-json/{endpoint}"
        response = requests.patch(
            url, auth=self.auth, headers=self.headers, json=data
        )
        return response

    def test_connection(self):
        """
        Tests the connection to WordPress.
        Returns True if connection is successful.
        Raises clear error messages for common failures.
        """
        try:
            response = self.get("wp/v2/users/me")

            if response.status_code == 200:
                data = response.json()
                print(f"[OK] Connected to WordPress")
                print(f"[OK] Logged in as: {data.get('name', 'unknown')}")
                print(f"[OK] User ID: {data.get('id', 'unknown')}")
                return True

            elif response.status_code == 401:
                print("[ERROR] 401 — Wrong username or Application Password")
                print("[ERROR] Check config.py credentials")
                return False

            elif response.status_code == 403:
                print("[ERROR] 403 — User does not have permission")
                print("[ERROR] Make sure the user has Administrator role")
                return False

            elif response.status_code == 404:
                print("[ERROR] 404 — WordPress URL not found")
                print(f"[ERROR] Check WP_URL in config.py: {self.base_url}")
                return False

            else:
                print(f"[ERROR] Unexpected status: {response.status_code}")
                print(f"[ERROR] Response: {response.text[:200]}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"[ERROR] Cannot connect to {self.base_url}")
            print("[ERROR] Is LocalWP running? Is the site started?")
            return False

    def get_site_info(self):
        """Returns basic site information."""
        response = self.get("")
        if response.status_code == 200:
            data = response.json()
            return {
                "name":        data.get("name"),
                "description": data.get("description"),
                "url":         data.get("url"),
            }
        return None


if __name__ == "__main__":
    import config

    client = WPClient(config.WP_URL, config.WP_USER, config.WP_PASSWORD)

    print("\n--- Testing WordPress connection ---")
    if client.test_connection():
        info = client.get_site_info()
        if info:
            print(f"\n[OK] Site name: {info['name']}")
            print(f"[OK] Site URL:  {info['url']}")