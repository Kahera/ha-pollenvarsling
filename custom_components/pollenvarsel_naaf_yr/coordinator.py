"""Data coordinator for NAAF Pollen Forecast integration."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_LANGUAGE, DEFAULT_UPDATE_FREQUENCY

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import PollenVarselConfigEntry

_LOGGER: logging.Logger = logging.getLogger(__name__)


class PollenDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for fetching pollen data."""

    config_entry: PollenVarselConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        language: str = DEFAULT_LANGUAGE,
        update_frequency: int = DEFAULT_UPDATE_FREQUENCY,
    ) -> None:
        """Initialize coordinator."""
        from datetime import timedelta
        
        super().__init__(
            hass,
            _LOGGER,
            name="NAAF Pollen Forecast Data",
            update_interval=timedelta(hours=update_frequency),
        )
        self.language = language
        self._update_frequency = update_frequency
        self._location_data: dict[str, dict[str, Any]] = {}
        self._pollen_names: dict[str, str] = {}
        self._translations: dict[str, Any] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """Load translations from language files."""
        component_dir = Path(__file__).parent

        def _load_json(path: Path) -> dict[str, Any]:
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as err:
                _LOGGER.warning("Failed to load translation file %s: %s", path, err)
                return {}

        def _resolve(directory: Path) -> Path:
            candidate = directory / f"{self.language}.json"
            return candidate if candidate.exists() else directory / "en.json"

        self._translations = _load_json(_resolve(component_dir / "translations"))
        self._translations.update(_load_json(_resolve(component_dir / "locale")))

    @property
    def location_data(self) -> dict[str, dict[str, Any]]:
        """Get location data."""
        return self._location_data

    @property
    def pollen_names(self) -> dict[str, str]:
        """Get pollen names mapping."""
        return self._pollen_names

    @property
    def translations(self) -> dict[str, Any]:
        """Get translations for current language."""
        return self._translations

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch pollen data from NAAF API for all locations."""
        import aiohttp
        from .const import CONF_LOCATION_ID, CONF_LOCATIONS, BASE_URL

        try:
            locations = self.config_entry.data.get(CONF_LOCATIONS, [])
            
            self._location_data = {}
            
            async with aiohttp.ClientSession() as session:
                for location in locations:
                    location_id = location.get(CONF_LOCATION_ID)
                    
                    try:
                        url = f"{BASE_URL}/{location_id}/pollen?language={self.language}"
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                            if resp.status != 200:
                                raise UpdateFailed(f"API returned {resp.status} for {location_id}")
                            data = await resp.json()

                        embedded = data.get("_embedded", {})
                        region_name = embedded.get("regionName", location_id)
                        
                        # Parse the response
                        forecast = embedded.get("pollenForecast", [])
                        parsed_data = {"today": {}, "tomorrow": {}}

                        for day_idx, day_forecast in enumerate(forecast[:2]):
                            day_key = "today" if day_idx == 0 else "tomorrow"
                            distributions = day_forecast.get("distributions", {})
                            date = day_forecast.get("date")

                            # Flatten the distribution structure
                            for level, level_data in distributions.items():
                                if "pollenTypes" in level_data:
                                    distribution_name = level_data.get("distributionName")
                                    for pollen in level_data["pollenTypes"]:
                                        pollen_id = pollen.get("id")
                                        pollen_name = pollen.get("name")
                                        if pollen_id:
                                            parsed_data[day_key][pollen_id] = {
                                                "level": level,
                                                "level_name": distribution_name,
                                                "pollen_name": pollen_name,
                                                "date": date,
                                            }
                                            if pollen_name:
                                                self._pollen_names[pollen_id] = pollen_name

                        self._location_data[location_id] = {
                            "region_name": region_name,
                            "data": parsed_data,
                            "last_updated": __import__("datetime").datetime.now().isoformat(),
                        }
                    except Exception as err:
                        _LOGGER.warning(
                            "Error fetching pollen data for location %s: %s",
                            location_id,
                            err,
                        )
                        raise UpdateFailed(f"Error fetching pollen data: {err}") from err

            return {"locations": self._location_data}

        except UpdateFailed as err:
            raise err
        except Exception as err:
            raise UpdateFailed(f"Error fetching pollen data: {err}") from err

