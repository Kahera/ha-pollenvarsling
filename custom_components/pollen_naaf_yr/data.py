"""Custom types for NAAF Pollen Forecast integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .coordinator import PollenDataCoordinator

type PollenVarselConfigEntry = ConfigEntry[PollenDataCoordinator]
