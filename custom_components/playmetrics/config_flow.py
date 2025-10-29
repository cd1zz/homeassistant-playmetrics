"""Config flow for Playmetrics integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .api import PlaymetricsApiClient, PlaymetricsApiError
from .const import (
    CONF_FUTURE_DAYS,
    CONF_ROLE_ID,
    CONF_UPDATE_INTERVAL_HOURS,
    DEFAULT_FUTURE_DAYS,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_ROLE_ID): cv.string,
        vol.Optional(CONF_FUTURE_DAYS, default=DEFAULT_FUTURE_DAYS): cv.positive_int,
        vol.Optional(CONF_UPDATE_INTERVAL_HOURS, default=DEFAULT_UPDATE_INTERVAL_HOURS): vol.All(
            cv.positive_int, vol.Range(min=1, max=24)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    client = PlaymetricsApiClient(
        email=data[CONF_EMAIL],
        password=data[CONF_PASSWORD],
        role_id=data[CONF_ROLE_ID],
    )

    # Test the connection
    try:
        await hass.async_add_executor_job(client.login)
        await hass.async_add_executor_job(client.get_access_key)
    except PlaymetricsApiError as err:
        _LOGGER.error("Failed to authenticate: %s", err)
        raise

    # Return info to be stored in the config entry
    return {"title": f"Playmetrics ({data[CONF_EMAIL]})"}


class PlaymetricsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Playmetrics."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except PlaymetricsApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_EMAIL])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
