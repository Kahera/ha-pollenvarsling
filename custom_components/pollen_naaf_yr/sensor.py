"""NAAF Pollen Forecast Sensors."""
import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_LANGUAGE,
    CONF_LOCATION_ID,
    CONF_LOCATION_NAME,
    CONF_LOCATIONS,
    CONF_POLLEN_TYPES,
    CONF_UPDATE_FREQUENCY,
    DEFAULT_LANGUAGE,
    DEFAULT_UPDATE_FREQUENCY,
    DOMAIN,
    TRANSLATIONS,
)
from .coordinator import PollenDataCoordinator

_LOGGER: logging.Logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up pollen sensors from config entry."""
    config_data = entry.data
    
    locations = config_data.get(CONF_LOCATIONS, [])
    pollen_types = config_data.get(CONF_POLLEN_TYPES, [])
    update_frequency = config_data.get(CONF_UPDATE_FREQUENCY, DEFAULT_UPDATE_FREQUENCY)
    language = config_data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

    # Get or create coordinators storage
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})
    coordinators = hass.data[DOMAIN][entry.entry_id].setdefault("coordinators", {})

    entities = []

    for location in locations:
        location_id = location.get(CONF_LOCATION_ID)
        custom_location_name = location.get(CONF_LOCATION_NAME)

        # Reuse existing coordinator or create a new one
        if location_id not in coordinators:
            coordinator = PollenDataCoordinator(hass, location_id, language, update_frequency)
            await coordinator.async_config_entry_first_refresh()
            coordinators[location_id] = coordinator
        else:
            coordinator = coordinators[location_id]
            # Update coordinator settings if they changed
            coordinator.language = language
            coordinator.update_interval = timedelta(hours=update_frequency)

        # Display name is custom name or region name from API
        display_name = custom_location_name or coordinator.region_name

        # Create device info for this location
        device_info = DeviceInfo(
            identifiers={(DOMAIN, location_id)},
            name=display_name,
            manufacturer="NAAF/Yr",
        )

        # Create sensors for each pollen type and forecast day
        for pollen_type in pollen_types:
            for day in ["today", "tomorrow"]:
                sensor = PollenSensor(
                    coordinator,
                    location_id,
                    custom_location_name,
                    pollen_type,
                    day,
                    entry.entry_id,
                    device_info,
                )
                entities.append(sensor)

    async_add_entities(entities, update_existing=True)


class PollenSensor(CoordinatorEntity, SensorEntity):
    """Sensor for pollen level."""

    _attr_attribution = "Data from NAAF (Norwegian Asthma and Allergy Association)"

    def __init__(
        self,
        coordinator: PollenDataCoordinator,
        location_id: str,
        custom_location_name: str | None,
        pollen_type: str,
        day: str,
        entry_id: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.pollen_type = pollen_type
        self.day = day
        self.location_id = location_id
        self.custom_location_name = custom_location_name
        self.entry_id = entry_id
        self._display_name = custom_location_name or coordinator.region_name

        self._attr_unique_id = (
            f"{DOMAIN}_{location_id}_{pollen_type.lower()}_{day}"
        )
        self._attr_device_info = device_info
        self._attr_icon = self._get_icon()

    @property
    def name(self) -> str:
        """Return localized sensor name."""
        language = self.coordinator.language
        translations = TRANSLATIONS.get(language, TRANSLATIONS["en"])
        day_text = translations[self.day]

        # Use localized pollen name from coordinator's name mapping
        pollen_name = self.coordinator.pollen_names.get(self.pollen_type, self.pollen_type)

        return f"{translations['pollen']} {pollen_name} {self._display_name} {day_text}"

    def _get_icon(self) -> str:
        """Get icon based on pollen type."""
        icons = {
            "hazel": "mdi:tree",
            "alder": "mdi:tree",
            "willow": "mdi:tree",
            "birch": "mdi:tree",
            "grass": "mdi:grass",
            "mugwort": "mdi:flower",
        }
        return icons.get(self.pollen_type.lower(), "mdi:flower-pollen")

    @property
    def state(self) -> str | None:
        """Return pollen level."""
        if not self.coordinator.data:
            return None

        day_data = self.coordinator.data.get(self.day, {})
        pollen_data = day_data.get(self.pollen_type, {})
        return pollen_data.get("level", "none")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        day_data = self.coordinator.data.get(self.day, {})
        pollen_data = day_data.get(self.pollen_type, {})

        attrs: dict[str, Any] = {
            "date": pollen_data.get("date"),
            "pollen_name": pollen_data.get("pollen_name"),
            "region_name": self.coordinator.region_name,
            "last_updated": self.coordinator.last_updated_at,
        }
        if pollen_data.get("level_name"):
            attrs["level_name"] = pollen_data.get("level_name")
        if self.custom_location_name:
            attrs["location_name"] = self.custom_location_name
        return attrs
