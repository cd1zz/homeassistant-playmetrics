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

# Firebase web API key used by the Playmetrics web app. Playmetrics rotates
# this key occasionally (the previous one expired 2026-09-15). This value is
# only a starting point: the client re-discovers the current key from the web
# app's config bundle whenever Google reports the key as invalid/expired.
DEFAULT_FIREBASE_API_KEY = "AIzaSyBzoJzZJ8flf7colzI0FjruUwJV_tqRj4M"

# API endpoints
API_FIREBASE_AUTH_TEMPLATE = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={key}"
)
API_LOGIN = "https://api.playmetrics.com/firebase/user/login"
API_CALENDAR = "https://api.playmetrics.com/user/calendars?populate=upcoming,team:itineraries"

# Playmetrics web app, used to discover the current Firebase API key
PLAYMETRICS_WEB_APP = "https://app.playmetrics.com/"

# Sensor
SENSOR_NAME = "Schedule"
ATTR_EVENTS = "events"
