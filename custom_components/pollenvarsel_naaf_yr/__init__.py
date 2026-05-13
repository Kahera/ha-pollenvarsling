"""NAAF Pollen Forecast Integration."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import CONF_LANGUAGE, CONF_UPDATE_FREQUENCY, DEFAULT_LANGUAGE, DEFAULT_UPDATE_FREQUENCY, DOMAIN
from .coordinator import PollenDataCoordinator
from .data import PollenVarselConfigEntry

_LOGGER: logging.Logger = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PollenVarselConfigEntry,
) -> bool:
    """Set up NAAF/Yr Pollen from config entry."""
    config_data = entry.data
    
    # Extract configuration
    update_frequency = config_data.get(CONF_UPDATE_FREQUENCY, DEFAULT_UPDATE_FREQUENCY)
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
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: PollenVarselConfigEntry,
) -> bool:
    """Unload config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: PollenVarselConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)

