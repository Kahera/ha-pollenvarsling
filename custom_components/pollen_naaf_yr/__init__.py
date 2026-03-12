"""NAAF Pollen Forecast Integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_LANGUAGE,
    CONF_POLLEN_TYPES,
    DOMAIN,
    VALID_LANGUAGES,
    VALID_POLLEN_TYPES,
)
from .coordinator import PollenDataCoordinator
from .data import PollenVarselConfigEntry

if TYPE_CHECKING:
    pass

_LOGGER: logging.Logger = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up NAAF/Yr Pollen from configuration.yaml."""
    if DOMAIN not in config:
        return True

    pollen_config = config[DOMAIN]

    # Validate pollen types
    pollen_types = pollen_config.get(CONF_POLLEN_TYPES, [])
    invalid_types = [t for t in pollen_types if t not in VALID_POLLEN_TYPES]
    if invalid_types:
        _LOGGER.warning(
            "Unsupported pollen type(s) removed: %s. Valid types are: %s",
            ", ".join(invalid_types),
            ", ".join(sorted(VALID_POLLEN_TYPES)),
        )
        pollen_config[CONF_POLLEN_TYPES] = [t for t in pollen_types if t in VALID_POLLEN_TYPES]

    # Validate language
    language = pollen_config.get(CONF_LANGUAGE, "nb")
    if language not in VALID_LANGUAGES:
        _LOGGER.warning(
            "Invalid language '%s'. Valid languages are: %s. Falling back to 'nb'",
            language,
            ", ".join(sorted(VALID_LANGUAGES)),
        )
        pollen_config[CONF_LANGUAGE] = "nb"

    # Forward setup to sensor platform
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data=pollen_config,
        )
    )
    
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PollenVarselConfigEntry,
) -> bool:
    """Set up NAAF/Yr Pollen from config entry."""
    config_data = entry.data
    
    # Extract configuration
    from .const import DEFAULT_LANGUAGE, DEFAULT_UPDATE_FREQUENCY
    
    update_frequency = config_data.get("update_frequency", DEFAULT_UPDATE_FREQUENCY)
    language = config_data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
    
    # Create coordinator
    coordinator = PollenDataCoordinator(
        hass=hass,
        language=language,
        update_frequency=update_frequency,
    )
    
    await coordinator.async_config_entry_first_refresh()
    
    entry.runtime_data = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: PollenVarselConfigEntry,
) -> bool:
    """Unload config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

