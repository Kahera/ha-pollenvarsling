"""Config flow for NAAF/Yr Pollen Forecast integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_LANGUAGE,
    CONF_LOCATION_ID,
    CONF_LOCATIONS,
    CONF_POLLEN_TYPES,
    CONF_UPDATE_FREQUENCY,
    DEFAULT_LANGUAGE,
    DEFAULT_UPDATE_FREQUENCY,
    DOMAIN,
    VALID_LANGUAGES,
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
                
                return self.async_create_entry(
                    title=f"NAAF/Yr Pollen - {location_id}",
                    data={
                        CONF_LOCATIONS: [{CONF_LOCATION_ID: location_id}],
                        CONF_POLLEN_TYPES: user_input.get(CONF_POLLEN_TYPES, list(VALID_POLLEN_TYPES)),
                        CONF_UPDATE_FREQUENCY: user_input.get(CONF_UPDATE_FREQUENCY, DEFAULT_UPDATE_FREQUENCY),
                        CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_LOCATION_ID,
                    description={"suggested_value": user_input.get(CONF_LOCATION_ID, "") if user_input else ""},
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        placeholder="e.g., 1-189277"
                    ),
                ),
                vol.Required(
                    CONF_POLLEN_TYPES,
                    default=list(VALID_POLLEN_TYPES),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"label": "Hazel", "value": "hazel"},
                            {"label": "Alder", "value": "alder"},
                            {"label": "Willow", "value": "willow"},
                            {"label": "Birch", "value": "birch"},
                            {"label": "Grass", "value": "grass"},
                            {"label": "Mugwort", "value": "mugwort"},
                        ],
                        multiple=True,
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
                        options=[
                            {"label": "Norwegian (Bokmål)", "value": "nb"},
                            {"label": "Norwegian (Nynorsk)", "value": "nn"},
                            {"label": "Northern Sámi", "value": "sme"},
                            {"label": "English", "value": "en"},
                        ]
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

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle import from YAML configuration."""
        # Check if entry with similar data already exists
        await self.async_set_unique_id(f"{DOMAIN}_yaml_import")
        self._abort_if_unique_id_configured()
        
        return self.async_create_entry(
            title="NAAF/Yr Pollen Forecast (Imported from YAML)",
            data=import_data,
        )