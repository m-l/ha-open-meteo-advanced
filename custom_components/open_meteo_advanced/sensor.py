"""Sensor platform for Open-Meteo Advanced."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_CURRENT_VARS,
    CONF_DAILY_VARS,
    CONF_HOURLY_VARS,
    CONF_MODEL,
    CONF_NAME,
    CURRENT_VARIABLES,
    DAILY_VARIABLES,
    DOMAIN,
    HOURLY_VARIABLES,
    VariableMeta,
    model_display_name,
)
from .coordinator import OpenMeteoCoordinator

_LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.const import EntityCategory
    _DIAGNOSTIC = EntityCategory.DIAGNOSTIC
except (ImportError, AttributeError):
    _DIAGNOSTIC = None

# Device classes that require a matching unit; fall back to None if unsupported by the HA version
_SAFE_DEVICE_CLASSES = {
    "temperature", "humidity", "atmospheric_pressure", "precipitation",
    "wind_speed", "distance", "duration", "timestamp", "irradiance", "moisture",
}


def _safe_device_class(dc: str | None) -> str | None:
    if dc is None:
        return None
    return dc if dc in _SAFE_DEVICE_CLASSES else None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: OpenMeteoCoordinator = hass.data[DOMAIN][entry.entry_id]
    opts: dict[str, Any] = {**entry.data, **entry.options}

    entities: list[Any] = [OpenMeteoModelSensor(coordinator, entry)]

    for var in opts.get(CONF_CURRENT_VARS, []):
        if meta := CURRENT_VARIABLES.get(var):
            entities.append(OpenMeteoSensor(coordinator, entry, "current", var, meta))

    for var in opts.get(CONF_HOURLY_VARS, []):
        if meta := HOURLY_VARIABLES.get(var):
            entities.append(OpenMeteoSensor(coordinator, entry, "hourly", var, meta))

    for var in opts.get(CONF_DAILY_VARS, []):
        if meta := DAILY_VARIABLES.get(var):
            entities.append(OpenMeteoSensor(coordinator, entry, "daily", var, meta))

    async_add_entities(entities)


class OpenMeteoSensor(CoordinatorEntity[OpenMeteoCoordinator], SensorEntity):
    """Single weather variable sensor backed by the coordinator."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: OpenMeteoCoordinator,
        entry: ConfigEntry,
        var_type: str,
        var_name: str,
        meta: VariableMeta,
    ) -> None:
        super().__init__(coordinator)
        self._var_type = var_type
        self._var_name = var_name
        self._data_key = f"{var_type}_{var_name}"
        self._forecast_key = f"{var_type}_{var_name}_forecast"

        location_name = entry.data.get(CONF_NAME, "Open-Meteo")
        type_label = {"current": "Current", "hourly": "Hourly", "daily": "Daily"}[var_type]

        self._attr_unique_id = f"{entry.entry_id}_{var_type}_{var_name}"
        self._attr_name = f"{meta.name} ({type_label})"
        self._attr_native_unit_of_measurement = meta.unit
        self._attr_device_class = _safe_device_class(meta.device_class)
        self._attr_icon = meta.icon

        # Timestamp sensors (sunrise/sunset) have no numeric state class
        if meta.device_class == "timestamp":
            self._attr_state_class = None

        model_id = entry.options.get(CONF_MODEL, entry.data.get(CONF_MODEL, "best_match"))
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=location_name,
            manufacturer="Open-Meteo",
            model=model_display_name(model_id),
            configuration_url="https://open-meteo.com/en/docs",
        )

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._data_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        forecast = self.coordinator.data.get(self._forecast_key)
        if forecast:
            return {"forecast": forecast}
        return {}


class OpenMeteoModelSensor(CoordinatorEntity[OpenMeteoCoordinator], SensorEntity):
    """Diagnostic sensor showing which forecast model is configured for this location.

    Always created, independent of variable selection, so it's visible even if
    the weather entity is disabled and no per-variable sensors are selected.
    """

    _attr_has_entity_name = True
    _attr_name = "Weather Model"
    _attr_icon = "mdi:weather-partly-cloudy"
    _attr_entity_category = _DIAGNOSTIC

    def __init__(self, coordinator: OpenMeteoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        location_name = entry.data.get(CONF_NAME, "Open-Meteo")

        self._attr_unique_id = f"{entry.entry_id}_weather_model"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=location_name,
            manufacturer="Open-Meteo",
            model=model_display_name(self._model_id),
            configuration_url="https://open-meteo.com/en/docs",
        )

    @property
    def _model_id(self) -> str:
        opts: dict[str, Any] = {**self._entry.data, **self._entry.options}
        return opts.get(CONF_MODEL, "best_match")

    @property
    def native_value(self) -> str:
        return model_display_name(self._model_id)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {"model_id": self._model_id}
        if self._model_id == "best_match":
            attrs["note"] = (
                "Best Match lets Open-Meteo auto-select a model per location; "
                "the API response does not report which underlying model was "
                "actually used for a given point in time."
            )
        return attrs
