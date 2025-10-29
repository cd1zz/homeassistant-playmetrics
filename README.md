# Playmetrics Home Assistant Integration

A Home Assistant custom component for integrating Playmetrics sports scheduling into your smart home.

## Features

- Fetches upcoming games, practices, and events from Playmetrics
- Displays events with team, location, and time information
- Shows cancelled events with clear markers
- Configurable look-ahead period (default 7 days)
- Automatic updates at configurable intervals

## Installation

### Manual Installation

1. Copy the `custom_components/playmetrics` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration -> Integrations
4. Click the "+ Add Integration" button
5. Search for "Playmetrics"
6. Follow the configuration steps

### HACS Installation (Future)

This integration can be added to HACS as a custom repository:

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Playmetrics" and install

## Configuration

During setup, you'll need to provide:

- **Email**: Your Playmetrics account email
- **Password**: Your Playmetrics account password
- **Role ID**: Your Playmetrics role ID (found in the app)
- **Days to look ahead**: Number of days to fetch events for (default: 7)
- **Update interval (hours)**: Hours between automatic updates (default: 6, range: 1-24)

### Finding Your Role ID

1. Log in to Playmetrics web app
2. Open your browser's developer tools (F12)
3. Go to the Network tab
4. Navigate to your schedule
5. Look for API calls to `api.playmetrics.com`
6. Find the `role_id` parameter in the request

## Usage

After configuration, a sensor will be created: `sensor.playmetrics_schedule`

### Sensor State

The sensor state shows the number of upcoming events, e.g., "3 events"

### Sensor Attributes

The sensor provides these attributes:

- `events`: List of formatted event strings
- `event_count`: Number of upcoming events
- `future_days`: Days being looked ahead
- `last_update`: Timestamp of last successful update

### Update Behavior

- **On Home Assistant startup/reboot**: Fresh data is fetched immediately from the Playmetrics API
- **Automatic updates**: Data refreshes every X hours based on your configured update interval
- **Entity persistence**: Sensor state and attributes persist through reboots

### Event Format

Each event in the `events` attribute is formatted as:

```
Day Mon DD, HH:MM AM/PM to HH:MM AM/PM | Event Title (Team Name) @ Location
```

Cancelled events include: ❌ CANCELLED

### Example Automation

```yaml
automation:
  - alias: "Notify of upcoming game"
    trigger:
      - platform: state
        entity_id: sensor.playmetrics_schedule
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.attributes.event_count > 0 }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Upcoming Playmetrics Events"
          message: >
            {{ trigger.to_state.attributes.events | join('\n') }}
```

### Lovelace Card Example

```yaml
type: markdown
content: |
  ## Playmetrics Schedule

  {% for event in state_attr('sensor.playmetrics_schedule', 'events') %}
  - {{ event }}
  {% endfor %}
```

## Troubleshooting

### Authentication Errors

- Verify your email and password are correct
- Ensure your Role ID is valid
- Check that you can log in to Playmetrics web app

### No Events Showing

- Verify you have events scheduled in Playmetrics
- Check the `future_days` setting
- Look at the sensor's `last_update` attribute

### API Errors

Check the Home Assistant logs for detailed error messages:
```
Configuration -> Logs -> Filter by "playmetrics"
```

## Support

For issues and feature requests, please open an issue on GitHub.

## License

This project is licensed under the Apache License 2.0.

## Disclaimer

This is an unofficial integration and is not affiliated with or endorsed by Playmetrics.
