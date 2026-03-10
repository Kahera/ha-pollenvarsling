"""NAAF Pollen Forecast Integration."""
import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

_LOGGER: logging.Logger = logging.getLogger(__name__)

DOMAIN: Final = "pollenvarsel_naaf_yr"
CONF_LOCATIONS: Final = "locations"
CONF_LOCATION_ID: Final = "location_id"
CONF_LOCATION_NAME: Final = "location_name"
CONF_POLLEN_TYPES: Final = "pollen_types"
CONF_UPDATE_FREQUENCY: Final = "update_frequency"
CONF_LANGUAGE: Final = "language"

VALID_POLLEN_TYPES: Final = {"hazel", "alder", "willow", "birch", "grass", "mugwort"}
VALID_LANGUAGES: Final = {"nb", "nn", "sme", "en"}

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up NAAF Pollen from configuration.yaml."""
    if DOMAIN not in config:
        return True

    hass.data.setdefault(DOMAIN, {})
    
    pollen_config = config[DOMAIN]

    # Validate pollen types
    pollen_types = pollen_config.get(CONF_POLLEN_TYPES, [])
    invalid_types = [t for t in pollen_types if t not in VALID_POLLEN_TYPES]
    if invalid_types:
        _LOGGER.error(
            "Invalid pollen type(s): %s. Valid types are: %s",
            ", ".join(invalid_types),
            ", ".join(sorted(VALID_POLLEN_TYPES)),
        )
        return False

    # Validate language
    language = pollen_config.get(CONF_LANGUAGE, "nb")
    if language not in VALID_LANGUAGES:
        _LOGGER.warning(
            "Invalid language '%s'. Valid languages are: %s. Falling back to 'nb'",
            language,
            ", ".join(sorted(VALID_LANGUAGES)),
        )
        pollen_config[CONF_LANGUAGE] = "nb"

    # Store config and forward setup
    hass.data[DOMAIN]["config"] = pollen_config
    
    # Forward setup to sensor platform
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data=pollen_config,
        )
    )
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NAAF Pollen from config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
        return True
    return False
