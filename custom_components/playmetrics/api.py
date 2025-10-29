"""Playmetrics API Client."""
from __future__ import annotations

import logging
from typing import Any

import requests

from .const import API_CALENDAR, API_FIREBASE_AUTH, API_LOGIN

_LOGGER = logging.getLogger(__name__)


class PlaymetricsApiError(Exception):
    """Exception for Playmetrics API errors."""


class PlaymetricsAuthError(PlaymetricsApiError):
    """Exception for authentication errors."""


class PlaymetricsApiClient:
    """Playmetrics API Client."""

    def __init__(self, email: str, password: str, role_id: str) -> None:
        """Initialize the API client."""
        self.email = email
        self.password = password
        self.role_id = role_id
        self.token: str | None = None
        self.access_key: str | None = None

    def login(self) -> None:
        """Authenticate with Playmetrics and get Firebase token."""
        _LOGGER.debug("Authenticating with Playmetrics...")

        payload = {
            "returnSecureToken": True,
            "email": self.email,
            "password": self.password,
            "clientType": "CLIENT_TYPE_WEB",
        }
        headers = {"Content-Type": "application/json"}

        try:
            resp = requests.post(
                API_FIREBASE_AUTH,
                json=payload,
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()
            self.token = resp.json()["idToken"]
            _LOGGER.debug("Authentication successful")
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Authentication failed: %s", err)
            raise PlaymetricsAuthError(f"Authentication failed: {err}") from err

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
