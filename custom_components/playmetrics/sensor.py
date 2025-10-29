"""Sensor platform for Playmetrics integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_EVENTS, DOMAIN, SENSOR_NAME
from .coordinator import PlaymetricsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Playmetrics sensor based on a config entry."""
    coordinator: PlaymetricsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([PlaymetricsScheduleSensor(coordinator, entry)], True)


class PlaymetricsScheduleSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Playmetrics Schedule Sensor."""

    def __init__(
        self,
        coordinator: PlaymetricsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"Playmetrics {SENSOR_NAME}"
        self._attr_unique_id = f"{entry.entry_id}_schedule"
        self._attr_icon = "mdi:calendar-multiple"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return "No data"

        event_count = self.coordinator.data.get("event_count", 0)
        if event_count == 0:
            return f"No events in next {self.coordinator.future_days} days"

        return f"{event_count} event{'s' if event_count != 1 else ''}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        events = self.coordinator.data.get("events", [])
        event_strings = []

        for evt in events:
            start: datetime = evt["start"]
            end: datetime | None = evt["end"]

            # Format time string
            start_str = start.strftime("%a %b %-d, %-I:%M %p")
            if end:
                end_str = end.strftime("%-I:%M %p")
                time_str = f"{start_str} to {end_str}"
            else:
                time_str = start_str

            # Add cancellation marker
            cancel_tag = " ❌ CANCELLED" if evt.get("cancelled") else ""

            # Build event line
            line = (
                f"{time_str} | {evt['title']} ({evt['team']}) "
                f"@ {evt['location']}{cancel_tag}"
            )
            event_strings.append(line)

        attributes = {
            ATTR_EVENTS: event_strings,
            "event_count": self.coordinator.data.get("event_count", 0),
            "future_days": self.coordinator.future_days,
        }

        if last_update := self.coordinator.data.get("last_update"):
            attributes["last_update"] = last_update.isoformat()

        return attributes

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success
