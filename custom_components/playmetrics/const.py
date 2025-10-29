"""Constants for the Playmetrics integration."""

DOMAIN = "playmetrics"

# Configuration keys
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_ROLE_ID = "role_id"
CONF_FUTURE_DAYS = "future_days"
CONF_UPDATE_INTERVAL_HOURS = "update_interval_hours"

# Defaults
DEFAULT_FUTURE_DAYS = 7
DEFAULT_UPDATE_INTERVAL_HOURS = 6

# API endpoints
API_FIREBASE_AUTH = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyBEB_rFRGuLJja2vzeDCa7J1NZp0E7RN4U"
API_LOGIN = "https://api.playmetrics.com/firebase/user/login"
API_CALENDAR = "https://api.playmetrics.com/user/calendars?populate=upcoming,team:itineraries"

# Sensor
SENSOR_NAME = "Schedule"
ATTR_EVENTS = "events"
