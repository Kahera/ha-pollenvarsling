"""Config flow for NAAF/Yr Pollen Forecast integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    BASE_URL,
    CONF_LANGUAGE,
    CONF_LOCATION_ID,
    CONF_LOCATION_NAME,
    CONF_LOCATIONS,
    CONF_POLLEN_TYPES,
    CONF_UPDATE_FREQUENCY,
    DEFAULT_LANGUAGE,
    DEFAULT_UPDATE_FREQUENCY,
    DOMAIN,
    VALID_POLLEN_TYPES,
)

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)


class PollenvarselConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NAAF/Yr Pollen Forecast."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        _errors = {}

        if user_input is not None:
            # Parse single location
            location_id = user_input.get(CONF_LOCATION_ID, "").strip().lower()
            if not location_id:
                _errors["base"] = "location_required"
            else:
                # Create unique ID based on location
                await self.async_set_unique_id(location_id)
                self._abort_if_unique_id_configured()
                
                # Get custom location name or fetch from API
                custom_location_name = user_input.get(CONF_LOCATION_NAME, "").strip()
                region_name = custom_location_name
                
                # If no custom name, try to fetch from API
                if not region_name:
                    try:
                        region_name = await self._async_fetch_region_name(
                            location_id, user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
                        )
                    except Exception as err:
                        _LOGGER.warning("Failed to fetch region name: %s", err)
                        region_name = location_id
                
                # Use region name or location_id as fallback
                display_name = region_name or location_id
                
                # Get translated title based on language selection
                language = user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
                title_text = self._get_entry_title(language)
                
                return self.async_create_entry(
                    title=f"{title_text} - {display_name}",
                    data={
                        CONF_LOCATIONS: [{CONF_LOCATION_ID: location_id, CONF_LOCATION_NAME: custom_location_name}],
                        CONF_POLLEN_TYPES: user_input.get(CONF_POLLEN_TYPES, list(VALID_POLLEN_TYPES)),
                        CONF_UPDATE_FREQUENCY: user_input.get(CONF_UPDATE_FREQUENCY, DEFAULT_UPDATE_FREQUENCY),
                        CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_LOCATION_ID): selector.TextSelector(),
                vol.Optional(CONF_LOCATION_NAME): selector.TextSelector(),
                vol.Required(
                    CONF_POLLEN_TYPES,
                    default=list(VALID_POLLEN_TYPES),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=list(VALID_POLLEN_TYPES),
                        multiple=True,
                        translation_key="pollen_type",
                    ),
                ),
                vol.Optional(
                    CONF_UPDATE_FREQUENCY,
                    default=DEFAULT_UPDATE_FREQUENCY,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1, max=24, step=1, unit_of_measurement="hours"
                    ),
                ),
                vol.Optional(
                    CONF_LANGUAGE,
                    default=DEFAULT_LANGUAGE,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["nb", "nn", "en"],
                        translation_key="language",
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=_errors,
            description_placeholders={
                "info": "Enter the Yr location ID (e.g., 1-189277)"
            },
        )

    def _get_entry_title(self, language: str) -> str:
        """Get translated entry title."""
        from pathlib import Path
        import json
        
        translations_dir = Path(__file__).parent / "translations"
        lang_file = translations_dir / f"{language}.json"
        
        # Fall back to English if language file doesn't exist
        if not lang_file.exists():
            lang_file = translations_dir / "en.json"
        
        try:
            with open(lang_file, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("entry", {}).get("title", "Pollen Forecast")
        except Exception as err:
            _LOGGER.debug("Error loading entry title translation: %s", err)
            return "Pollen Forecast"

    async def _async_fetch_region_name(self, location_id: str, language: str) -> str:
        """Fetch region name from API."""
        try:
            url = f"{BASE_URL}/{location_id}/pollen?language={language}"
            session = async_get_clientsession(self.hass)
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    region_name = data.get("_embedded", {}).get("regionName")
                    if region_name:
                        return region_name
        except Exception as err:
            _LOGGER.debug("Error fetching region name: %s", err)
        return ""

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle import from YAML configuration."""
        # Check if entry with similar data already exists
        await self.async_set_unique_id(f"{DOMAIN}_yaml_import")
        self._abort_if_unique_id_configured()
        
        return self.async_create_entry(
            title="NAAF/Yr Pollen Forecast (Imported from YAML)",
            data=import_data,
        )