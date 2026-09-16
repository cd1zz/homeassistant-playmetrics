"""Playmetrics API Client."""
from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urljoin

import requests

from .const import (
    API_CALENDAR,
    API_FIREBASE_AUTH_TEMPLATE,
    API_LOGIN,
    DEFAULT_FIREBASE_API_KEY,
    PLAYMETRICS_WEB_APP,
)

_LOGGER = logging.getLogger(__name__)

_FIREBASE_KEY_RE = re.compile(r"AIza[0-9A-Za-z_-]{35}")
_CONFIG_APIKEY_RE = re.compile(r"apiKey\s*:\s*[\"'](AIza[0-9A-Za-z_-]{35})[\"']")
_MAIN_BUNDLE_RE = re.compile(r"[\"'](?:\./|/)?(assets/v2/main-[^\"']+\.js)[\"']")
_CONFIG_BUNDLE_RE = re.compile(r"[\"'](?:\./|/)?(assets/v2/config-[^\"']+\.js)[\"']")


class PlaymetricsApiError(Exception):
    """Exception for Playmetrics API errors."""


class PlaymetricsAuthError(PlaymetricsApiError):
    """Exception for authentication errors."""


class PlaymetricsApiClient:
    """Playmetrics API Client."""

    # Shared across instances so the config flow and the coordinator both
    # benefit from a key discovered by either of them.
    _discovered_api_key: str | None = None

    def __init__(self, email: str, password: str, role_id: str) -> None:
        """Initialize the API client."""
        self.email = email
        self.password = password
        self.role_id = role_id
        self.token: str | None = None
        self.access_key: str | None = None

    @property
    def api_key(self) -> str:
        """Return the Firebase API key currently in use."""
        return PlaymetricsApiClient._discovered_api_key or DEFAULT_FIREBASE_API_KEY

    # ------------------------------------------------------------------
    # Firebase API key discovery
    # ------------------------------------------------------------------
    @staticmethod
    def _fetch_text(url: str) -> str | None:
        """GET a URL and return its body, or None on failure."""
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as err:
            _LOGGER.debug("Failed to fetch %s: %s", url, err)
            return None

    def discover_api_key(self) -> str | None:
        """Discover the current Firebase API key from the Playmetrics web app.

        The web app is a Vite bundle. index.html references a main-*.js chunk,
        which references a config-*.js chunk containing the Firebase config
        (apiKey, authDomain, projectId, ...). Fall back to scanning each
        fetched document for anything that looks like a Google API key.
        """
        _LOGGER.debug("Discovering Playmetrics Firebase API key from web app")

        html = self._fetch_text(PLAYMETRICS_WEB_APP)
        if not html:
            return None

        documents: list[str] = [html]

        main_match = _MAIN_BUNDLE_RE.search(html)
        if main_match:
            main_js = self._fetch_text(urljoin(PLAYMETRICS_WEB_APP, main_match.group(1)))
            if main_js:
                documents.append(main_js)
                config_match = _CONFIG_BUNDLE_RE.search(main_js)
                if config_match:
                    config_js = self._fetch_text(
                        urljoin(PLAYMETRICS_WEB_APP, config_match.group(1))
                    )
                    if config_js:
                        # Preferred: the explicit Firebase config object.
                        if key_match := _CONFIG_APIKEY_RE.search(config_js):
                            return key_match.group(1)
                        documents.append(config_js)

        # Fallback: any Google API key found in the documents we fetched.
        for doc in documents:
            if key_match := _FIREBASE_KEY_RE.search(doc):
                return key_match.group(0)

        _LOGGER.warning("Could not find a Firebase API key in the Playmetrics web app")
        return None

    def _refresh_api_key(self) -> bool:
        """Re-discover the API key. Return True if a different key was found."""
        new_key = self.discover_api_key()
        if not new_key or new_key == self.api_key:
            return False
        _LOGGER.info("Playmetrics Firebase API key rotated; using newly discovered key")
        PlaymetricsApiClient._discovered_api_key = new_key
        return True

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    @staticmethod
    def _firebase_error(resp: requests.Response) -> str:
        """Extract the Firebase error message from a failed response."""
        try:
            return str(resp.json()["error"]["message"])
        except (ValueError, KeyError, TypeError):
            return f"HTTP {resp.status_code}"

    def _firebase_sign_in(self) -> requests.Response:
        """POST credentials to Firebase using the current API key."""
        payload = {
            "returnSecureToken": True,
            "email": self.email,
            "password": self.password,
            "clientType": "CLIENT_TYPE_WEB",
        }
        headers = {"Content-Type": "application/json"}
        return requests.post(
            API_FIREBASE_AUTH_TEMPLATE.format(key=self.api_key),
            json=payload,
            headers=headers,
            timeout=10,
        )

    def login(self) -> None:
        """Authenticate with Playmetrics and get Firebase token.

        If Google rejects the API key (expired or invalid), re-discover the
        key from the Playmetrics web app and retry once.
        """
        _LOGGER.debug("Authenticating with Playmetrics...")

        try:
            resp = self._firebase_sign_in()
            if resp.status_code != 200:
                error = self._firebase_error(resp)
                if "API key" in error or "API_KEY" in error:
                    _LOGGER.warning(
                        "Firebase rejected the API key (%s); attempting to discover the current key",
                        error,
                    )
                    if self._refresh_api_key():
                        resp = self._firebase_sign_in()
                        if resp.status_code != 200:
                            error = self._firebase_error(resp)
                if resp.status_code != 200:
                    _LOGGER.error("Authentication failed: %s", error)
                    raise PlaymetricsAuthError(f"Authentication failed: {error}")

            self.token = resp.json()["idToken"]
            _LOGGER.debug("Authentication successful")
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise PlaymetricsAuthError(f"Authentication failed: {err}") from err
        except (ValueError, KeyError) as err:
            _LOGGER.error("Unexpected authentication response: %s", err)
            raise PlaymetricsAuthError("Unexpected authentication response") from err

    def get_access_key(self) -> None:
        """Get Playmetrics access key using Firebase token."""
        if not self.token:
            raise PlaymetricsAuthError("No Firebase token available")

        _LOGGER.debug("Requesting Playmetrics access key...")

        payload = {
            "current_role_id": self.role_id,
            "client_type": "desktop",
        }
        headers = {
            "Content-Type": "application/json",
            "Firebase-Token": self.token,
        }

        try:
            resp = requests.post(
                API_LOGIN,
                json=payload,
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()
            self.access_key = resp.json()["access_key"]
            _LOGGER.debug("Access key retrieved")
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Failed to get access key: %s", err)
            raise PlaymetricsApiError(f"Failed to get access key: {err}") from err

    def get_schedule(self) -> list[dict[str, Any]]:
        """Fetch schedule from Playmetrics API."""
        _LOGGER.debug("Fetching schedule from Playmetrics...")

        # Ensure we have valid credentials
        self.login()
        self.get_access_key()

        if not self.access_key or not self.token:
            raise PlaymetricsAuthError("Missing access credentials")

        headers = {
            "Pm-Access-Key": self.access_key,
            "Firebase-Token": self.token,
        }

        try:
            resp = requests.get(
                API_CALENDAR,
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()
            _LOGGER.debug("Schedule fetched successfully")
            return resp.json()
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Failed to fetch schedule: %s", err)
            raise PlaymetricsApiError(f"Failed to fetch schedule: {err}") from err

    async def async_test_connection(self) -> bool:
        """Test the API connection and credentials."""
        try:
            self.login()
            self.get_access_key()
            return True
        except PlaymetricsApiError:
            return False
