"""Config flow for NAAF/Yr Pollen Forecast integration."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector

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
    VALID_LANGUAGES,
    VALID_POLLEN_TYPES,
)

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)


class PollenvarselConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NAAF/Yr Pollen Forecast."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        super().__init__()
        self.locations: list[dict[str, str]] = []

    async def _validate_location(self, location_id: str) -> tuple[bool, str | None]:
        """Validate location ID by trying to fetch data from API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{BASE_URL}/{location_id}/pollen?language=nb"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        region_name = data.get("_embedded", {}).get("regionName")
                        if region_name:
                            return True, region_name
                        return True, None
                    elif resp.status == 404:
                        return False, "Location not found"
                    else:
                        return False, f"API returned status {resp.status}"
        except asyncio.TimeoutError:
            return False, "API request timed out"
        except Exception as err:
            return False, f"Error validating location: {err}"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - add location."""
        errors = {}
        
        if user_input is not None:
            location_id = user_input[CONF_LOCATION_ID].strip().lower()
            
            # Validate location
            is_valid, error_msg = await self._validate_location(location_id)
            if not is_valid:
                errors["base"] = error_msg or "Invalid location ID"
            else:
                location = {
                    CONF_LOCATION_ID: location_id,
                }
                if user_input.get(CONF_LOCATION_NAME):
                    location[CONF_LOCATION_NAME] = user_input[CONF_LOCATION_NAME]
                
                self.locations.append(location)
                
                # Ask if they want to add more locations
                return await self.async_step_add_location_confirm()

        schema = vol.Schema(
            {
                vol.Required(CONF_LOCATION_ID): selector.TextSelector(
                    selector.TextSelectorConfig(
                        placeholder="e.g., indre-østlandet"
                    ),
                ),
                vol.Optional(CONF_LOCATION_NAME): selector.TextSelector(
                    selector.TextSelectorConfig(
                        placeholder="Custom name (optional)"
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "info": "Enter the Yr location ID (e.g., indre-østlandet, molde)"
            },
        )

    async def async_step_add_location_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask if user wants to add another location."""
        if user_input is not None:
            if user_input.get("add_another"):
                return await self.async_step_add_location()
            else:
                return await self.async_step_configure()

        return self.async_show_form(
            step_id="add_location_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required("add_another", default=False): selector.BooleanSelector(),
                }
            ),
            description_placeholders={
                "locations": ", ".join(
                    [loc.get(CONF_LOCATION_NAME, loc[CONF_LOCATION_ID]) for loc in self.locations]
                )
            },
        )

    async def async_step_add_location(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle adding another location."""
        errors = {}
        
        if user_input is not None:
            location_id = user_input[CONF_LOCATION_ID].strip().lower()
            
            # Validate location
            is_valid, error_msg = await self._validate_location(location_id)
            if not is_valid:
                errors["base"] = error_msg or "Invalid location ID"
            else:
                location = {
                    CONF_LOCATION_ID: location_id,
                }
                if user_input.get(CONF_LOCATION_NAME):
                    location[CONF_LOCATION_NAME] = user_input[CONF_LOCATION_NAME]
                
                self.locations.append(location)
                return await self.async_step_add_location_confirm()

        schema = vol.Schema(
            {
                vol.Required(CONF_LOCATION_ID): selector.TextSelector(
                    selector.TextSelectorConfig(
                        placeholder="e.g., molde, østlandet-med-oslo"
                    ),
                ),
                vol.Optional(CONF_LOCATION_NAME): selector.TextSelector(
                    selector.TextSelectorConfig(
                        placeholder="Custom name (optional)"
                    ),
                ),
            }
        )

        return self.async_show_form(
            step_id="add_location",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle pollen types, frequency, and language configuration."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"NAAF/Yr Pollen Forecast - {', '.join([loc.get(CONF_LOCATION_NAME, loc[CONF_LOCATION_ID]) for loc in self.locations])}",
                data={
                    CONF_LOCATIONS: self.locations,
                    CONF_POLLEN_TYPES: user_input.get(CONF_POLLEN_TYPES, list(VALID_POLLEN_TYPES)),
                    CONF_UPDATE_FREQUENCY: user_input.get(CONF_UPDATE_FREQUENCY, DEFAULT_UPDATE_FREQUENCY),
                    CONF_LANGUAGE: user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                },
            )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POLLEN_TYPES, default=list(VALID_POLLEN_TYPES)
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
                    CONF_UPDATE_FREQUENCY, default=DEFAULT_UPDATE_FREQUENCY
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1, max=24, step=1, unit_of_measurement="hours"
                    ),
                ),
                vol.Optional(
                    CONF_LANGUAGE, default=DEFAULT_LANGUAGE
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
            step_id="configure",
            data_schema=schema,
            description_placeholders={
                "info": "Configure pollen types, update frequency, and language"
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



