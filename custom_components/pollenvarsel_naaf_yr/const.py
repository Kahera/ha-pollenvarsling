"""Constants for NAAF Pollen Forecast integration."""
from typing import Final

DOMAIN: Final = "pollenvarsel_naaf_yr"

# Configuration keys
CONF_LOCATIONS: Final = "locations"
CONF_LOCATION_ID: Final = "location_id"
CONF_LOCATION_NAME: Final = "location_name"
CONF_POLLEN_TYPES: Final = "pollen_types"
CONF_UPDATE_FREQUENCY: Final = "update_frequency"
CONF_LANGUAGE: Final = "language"

# Valid values
VALID_POLLEN_TYPES: Final = {"hazel", "alder", "salix", "birch", "grass", "mugwort"}
VALID_LANGUAGES: Final = {"nb", "nn", "en"}

# Defaults
DEFAULT_UPDATE_FREQUENCY: Final = 3
DEFAULT_LANGUAGE: Final = "nb"

# API
BASE_URL: Final = "https://www.yr.no/api/v0/locations"
