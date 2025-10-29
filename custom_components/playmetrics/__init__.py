"""The Playmetrics integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant

from .api import PlaymetricsApiClient
from .const import (
    CONF_FUTURE_DAYS,
    CONF_ROLE_ID,
    CONF_UPDATE_INTERVAL_HOURS,
    DEFAULT_FUTURE_DAYS,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DOMAIN,
)
from .coordinator import PlaymetricsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Playmetrics from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create API client
    client = PlaymetricsApiClient(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        role_id=entry.data[CONF_ROLE_ID],
    )

    # Get configuration
    future_days = entry.data.get(CONF_FUTURE_DAYS, DEFAULT_FUTURE_DAYS)
    update_interval_hours = entry.data.get(
        CONF_UPDATE_INTERVAL_HOURS, DEFAULT_UPDATE_INTERVAL_HOURS
    )

    # Create update coordinator with configured update interval
    update_interval = timedelta(hours=update_interval_hours)
    coordinator = PlaymetricsDataUpdateCoordinator(
        hass,
        client,
        future_days,
        update_interval,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
