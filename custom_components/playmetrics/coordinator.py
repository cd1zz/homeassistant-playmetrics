"""DataUpdateCoordinator for Playmetrics."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import PlaymetricsApiClient, PlaymetricsApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PlaymetricsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Playmetrics data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: PlaymetricsApiClient,
        future_days: int,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.future_days = future_days

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Playmetrics API."""
        try:
            # Fetch schedule from API (run in executor since it's blocking)
            teams = await self.hass.async_add_executor_job(self.client.get_schedule)

            # Process events
            all_events = []
            now = dt_util.now()
            future_date = now + timedelta(days=self.future_days)

            for team in teams:
                team_name = team.get("name", "Unknown Team")
                for evt in team.get("events", []):
                    start_str = evt.get("start_datetime")
                    end_str = evt.get("end_datetime")
                    if not start_str:
                        continue

                    # Parse datetime strings
                    start_dt = dt_util.parse_datetime(start_str)
                    end_dt = dt_util.parse_datetime(end_str) if end_str else None

                    if start_dt is None:
                        continue

                    # Make timezone aware if needed
                    if start_dt.tzinfo is None:
                        start_dt = dt_util.as_local(start_dt)
                    if end_dt and end_dt.tzinfo is None:
                        end_dt = dt_util.as_local(end_dt)

                    # Filter events within the date range
                    if now <= start_dt <= future_date:
                        title = evt.get("summary", "Event")
                        details = evt.get("details", {})

                        # Get location based on event type
                        if evt.get("type") == "Practice":
                            # For practices, try description first, then field display_name
                            location = details.get("description") or details.get(
                                "field", {}
                            ).get("display_name", "TBD")
                        else:
                            # For games and other events, use location or field display_name
                            location = details.get("location") or details.get(
                                "field", {}
                            ).get("display_name", "TBD")

                        cancelled = details.get("canceled_at") is not None

                        all_events.append(
                            {
                                "start": start_dt,
                                "end": end_dt,
                                "title": title,
                                "team": team_name,
                                "location": location,
                                "cancelled": cancelled,
                                "type": evt.get("type", "Event"),
                            }
                        )

            # Sort events chronologically
            all_events.sort(key=lambda e: e["start"])

            return {
                "events": all_events,
                "event_count": len(all_events),
                "last_update": now,
            }

        except PlaymetricsApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
