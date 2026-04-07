"""NAAF Pollen Forecast Sensors."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    CONF_LOCATION_ID,
    CONF_LOCATION_NAME,
    CONF_LOCATIONS,
    CONF_POLLEN_TYPES,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import PollenVarselConfigEntry

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PollenVarselConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up pollen sensors from config entry."""
    coordinator = entry.runtime_data
    config_data = entry.data
    
    locations = config_data.get(CONF_LOCATIONS, [])
    pollen_types = config_data.get(CONF_POLLEN_TYPES, [])

    entities: list[PollenSensor] = []

    for location in locations:
        location_id = location.get(CONF_LOCATION_ID)
        custom_location_name = location.get(CONF_LOCATION_NAME)

        # Get region name from coordinator data
        location_data = coordinator.location_data.get(location_id, {})
        region_name = location_data.get("region_name", location_id)
        display_name = custom_location_name or region_name

        # Create device info for this location
        device_info = DeviceInfo(
            identifiers={(DOMAIN, location_id)},
            name=display_name,
            manufacturer="NAAF/Yr",
        )

        # Create sensors for each pollen type and forecast day
        for pollen_type in pollen_types:
            for day in ["today", "tomorrow"]:
                entity = PollenSensor(
                    coordinator=coordinator,
                    entry_id=entry.entry_id,
                    location_id=location_id,
                    custom_location_name=custom_location_name,
                    pollen_type=pollen_type,
                    day=day,
                    device_info=device_info,
                )
                entities.append(entity)

    async_add_entities(entities)


class PollenSensor(CoordinatorEntity, SensorEntity):
    """Sensor for pollen level."""

    _attr_attribution = "Data from NAAF (Norwegian Asthma and Allergy Association)"

    def __init__(
        self,
        coordinator,
        entry_id: str,
        location_id: str,
        custom_location_name: str | None,
        pollen_type: str,
        day: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.pollen_type = pollen_type
        self.day = day
        self.location_id = location_id
        self.custom_location_name = custom_location_name

        region_name = coordinator.location_data.get(location_id, {}).get(
            "region_name", location_id
        )
        self._display_name = custom_location_name or region_name

        self._attr_unique_id = (
            f"{entry_id}_{location_id}_{pollen_type.lower()}_{day}"
        )
        self.entity_id = f"sensor.pollen_{pollen_type}_{slugify(self._display_name)}_{day}"
        self._attr_device_info = device_info
        self._attr_icon = self._get_icon()

    @property
    def name(self) -> str:
        """Return localized sensor name."""
        translations = self.coordinator.translations
        
        # Get localized day name from translations
        general = translations.get("general", {})
        day_text = general.get(self.day, self.day.lower())
        
        # Get localized pollen name from translations
        selector = translations.get("selector", {})
        pollen_labels = selector.get("pollen_type", {}).get("options", {})
        pollen_name = pollen_labels.get(self.pollen_type, self.pollen_type.capitalize())
        
        return f"{pollen_name} {day_text} ({self._display_name})"

    def _get_icon(self) -> str:
        """Get icon based on pollen type."""
        icons = {
            "hazel": "mdi:tree",
            "alder": "mdi:tree",
            "salix": "mdi:tree",
            "birch": "mdi:tree",
            "grass": "mdi:grass",
            "mugwort": "mdi:flower",
        }
        return icons.get(self.pollen_type.lower(), "mdi:flower-pollen")

    @property
    def state(self) -> str | None:
        """Return pollen level."""
        location_data = self.coordinator.location_data.get(self.location_id, {})
        day_data = location_data.get("data", {}).get(self.day, {})
        pollen_data = day_data.get(self.pollen_type, {})
        return pollen_data.get("level", "none")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        location_data = self.coordinator.location_data.get(self.location_id, {})
        day_data = location_data.get("data", {}).get(self.day, {})
        pollen_data = day_data.get(self.pollen_type, {})

        attrs: dict[str, Any] = {
            "date": pollen_data.get("date"),
            "pollen_name": pollen_data.get("pollen_name"),
            "region_name": location_data.get("region_name"),
            "last_updated": location_data.get("last_updated"),
        }
        level_name = pollen_data.get("level_name")
        if not level_name:
            level = pollen_data.get("level") or "none"
            levels_translations = self.coordinator.translations.get("levels", {})
            level_key = str(level).lower()
            level_name = levels_translations.get(level_key) or str(level)
        attrs["level_name"] = level_name
        if self.custom_location_name:
            attrs["location_name"] = self.custom_location_name
        return attrs

