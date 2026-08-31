"""DataUpdateCoordinator for Open-Meteo Advanced."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE_URL,
    CONF_CURRENT_VARS,
    CONF_DAILY_VARS,
    CONF_FORECAST_DAYS,
    CONF_HOURLY_VARS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MODEL,
    CONF_PAST_DAYS,
    CONF_WEATHER_ENTITY,
    DEFAULT_FORECAST_DAYS,
    DOMAIN,
    WEATHER_CURRENT_VARS,
    WEATHER_DAILY_VARS,
    WEATHER_HOURLY_VARS,
    wmo_to_ha_condition,
)

_LOGGER = logging.getLogger(__name__)


class OpenMeteoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches data from Open-Meteo API and exposes it per-variable."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        update_interval: timedelta,
    ) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)
        self.entry = entry
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict[str, Any]:
        opts: dict[str, Any] = {**self.entry.data, **self.entry.options}

        user_hourly: list[str] = opts.get(CONF_HOURLY_VARS, [])
        user_daily: list[str] = opts.get(CONF_DAILY_VARS, [])
        user_current: list[str] = opts.get(CONF_CURRENT_VARS, [])
        weather_entity: bool = opts.get(CONF_WEATHER_ENTITY, False)

        # Merge user-selected vars with weather-entity vars (deduplicated)
        if weather_entity:
            hourly_vars = list(dict.fromkeys(user_hourly + WEATHER_HOURLY_VARS))
            daily_vars = list(dict.fromkeys(user_daily + WEATHER_DAILY_VARS))
            current_vars = list(dict.fromkeys(user_current + WEATHER_CURRENT_VARS))
        else:
            hourly_vars = user_hourly
            daily_vars = user_daily
            current_vars = user_current

        if not hourly_vars and not daily_vars and not current_vars:
            return {}

        params: dict[str, Any] = {
            "latitude": opts[CONF_LATITUDE],
            "longitude": opts[CONF_LONGITUDE],
            "timezone": "auto",
            "wind_speed_unit": "kmh",
            "forecast_days": opts.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS),
            "past_days": opts.get(CONF_PAST_DAYS, 0),
        }

        model = opts.get(CONF_MODEL, "best_match")
        if model != "best_match":
            params["models"] = model

        if hourly_vars:
            params["hourly"] = ",".join(hourly_vars)
        if daily_vars:
            params["daily"] = ",".join(daily_vars)
        if current_vars:
            params["current"] = ",".join(current_vars)

        try:
            async with self._session.get(
                API_BASE_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise UpdateFailed(f"API error {resp.status}: {body[:200]}")
                raw = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Connection error: {err}") from err

        result = self._parse_sensors(raw, opts, user_hourly, user_daily, user_current)

        if weather_entity:
            result["_weather"] = self._parse_weather(raw, opts)

        return result

    # ------------------------------------------------------------------
    # Sensor data parsing
    # ------------------------------------------------------------------

    def _parse_sensors(
        self,
        raw: dict[str, Any],
        opts: dict[str, Any],
        hourly_vars: list[str],
        daily_vars: list[str],
        current_vars: list[str],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        now = datetime.now()
        forecast_days = int(opts.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS))
        # Hourly forecast length follows the configured forecast_days, same as
        # what Open-Meteo actually returns - previously hardcoded to 48h (2 days),
        # which silently truncated hourly-only consumers (e.g. cards that build
        # a multi-day view purely from the hourly forecast) regardless of this
        # entry's actual Forecast days setting.
        max_hourly = forecast_days * 24
        max_daily = forecast_days

        if current_vars and "current" in raw:
            current = raw["current"]
            for var in current_vars:
                result[f"current_{var}"] = current.get(var)

        if hourly_vars and "hourly" in raw:
            hourly = raw["hourly"]
            times: list[str] = hourly.get("time", [])
            current_hour = now.strftime("%Y-%m-%dT%H:00")

            idx = next((i for i, t in enumerate(times) if t == current_hour), None)
            if idx is None:
                for i, t in enumerate(times):
                    if t <= current_hour:
                        idx = i

            for var in hourly_vars:
                values: list = hourly.get(var, [])
                result[f"hourly_{var}"] = values[idx] if idx is not None and idx < len(values) else None
                if idx is not None:
                    end = min(idx + max_hourly, len(times))
                    result[f"hourly_{var}_forecast"] = [
                        {"time": times[i], "value": values[i] if i < len(values) else None}
                        for i in range(idx, end)
                    ]

        if daily_vars and "daily" in raw:
            daily = raw["daily"]
            times = daily.get("time", [])
            today = now.strftime("%Y-%m-%d")

            idx = next((i for i, t in enumerate(times) if t == today), None)
            if idx is None and times:
                idx = 0

            for var in daily_vars:
                values = daily.get(var, [])
                result[f"daily_{var}"] = values[idx] if idx is not None and idx < len(values) else None
                if idx is not None:
                    end = min(idx + max_daily, len(times))
                    result[f"daily_{var}_forecast"] = [
                        {"time": times[i], "value": values[i] if i < len(values) else None}
                        for i in range(idx, end)
                    ]

        return result

    # ------------------------------------------------------------------
    # Weather entity data parsing
    # ------------------------------------------------------------------

    def _parse_weather(self, raw: dict[str, Any], opts: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now()
        forecast_days = int(opts.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS))
        max_hourly = forecast_days * 24
        max_daily = forecast_days
        current_raw = raw.get("current", {})

        weather: dict[str, Any] = {
            "temperature": current_raw.get("temperature_2m"),
            "humidity": current_raw.get("relative_humidity_2m"),
            "apparent_temperature": current_raw.get("apparent_temperature"),
            "wind_speed": current_raw.get("wind_speed_10m"),
            "wind_bearing": current_raw.get("wind_direction_10m"),
            "wind_gust_speed": current_raw.get("wind_gusts_10m"),
            "pressure": current_raw.get("pressure_msl"),
            "cloud_coverage": current_raw.get("cloud_cover"),
            "visibility": _m_to_km(current_raw.get("visibility")),
            "condition": wmo_to_ha_condition(
                current_raw.get("weather_code"),
                current_raw.get("is_day", 1),
            ),
            "hourly_forecast": [],
            "daily_forecast": [],
        }

        # Hourly forecast
        hourly_raw = raw.get("hourly", {})
        h_times = hourly_raw.get("time", [])
        if h_times:
            current_hour = now.strftime("%Y-%m-%dT%H:00")
            start = next((i for i, t in enumerate(h_times) if t >= current_hour), 0)
            end = min(start + max_hourly, len(h_times))

            h_temp = hourly_raw.get("temperature_2m", [])
            h_code = hourly_raw.get("weather_code", [])
            h_wind = hourly_raw.get("wind_speed_10m", [])
            h_bearing = hourly_raw.get("wind_direction_10m", [])
            h_precip_prob = hourly_raw.get("precipitation_probability", [])
            h_precip = hourly_raw.get("precipitation", [])
            h_pressure = hourly_raw.get("pressure_msl", [])
            h_cloud = hourly_raw.get("cloud_cover", [])
            h_humidity = hourly_raw.get("relative_humidity_2m", [])

            for i in range(start, end):
                code = h_code[i] if i < len(h_code) else None
                # Assume day for hourly forecasts (no is_day in hourly by default)
                weather["hourly_forecast"].append({
                    "datetime": f"{h_times[i]}:00",
                    "condition": wmo_to_ha_condition(code),
                    "native_temperature": h_temp[i] if i < len(h_temp) else None,
                    "native_wind_speed": h_wind[i] if i < len(h_wind) else None,
                    "wind_bearing": h_bearing[i] if i < len(h_bearing) else None,
                    "precipitation_probability": h_precip_prob[i] if i < len(h_precip_prob) else None,
                    "native_precipitation": h_precip[i] if i < len(h_precip) else None,
                    "native_pressure": h_pressure[i] if i < len(h_pressure) else None,
                    "cloud_coverage": h_cloud[i] if i < len(h_cloud) else None,
                    "humidity": h_humidity[i] if i < len(h_humidity) else None,
                })

        # Daily forecast
        daily_raw = raw.get("daily", {})
        d_times = daily_raw.get("time", [])
        if d_times:
            today = now.strftime("%Y-%m-%d")
            start = next((i for i, t in enumerate(d_times) if t >= today), 0)
            end = min(start + max_daily, len(d_times))

            d_max = daily_raw.get("temperature_2m_max", [])
            d_min = daily_raw.get("temperature_2m_min", [])
            d_code = daily_raw.get("weather_code", [])
            d_wind = daily_raw.get("wind_speed_10m_max", [])
            d_bearing = daily_raw.get("wind_direction_10m_dominant", [])
            d_precip = daily_raw.get("precipitation_sum", [])
            d_precip_prob = daily_raw.get("precipitation_probability_max", [])

            for i in range(start, end):
                code = d_code[i] if i < len(d_code) else None
                weather["daily_forecast"].append({
                    "datetime": f"{d_times[i]}T00:00:00",
                    "condition": wmo_to_ha_condition(code),
                    "native_temperature": d_max[i] if i < len(d_max) else None,
                    "native_templow": d_min[i] if i < len(d_min) else None,
                    "native_wind_speed": d_wind[i] if i < len(d_wind) else None,
                    "wind_bearing": d_bearing[i] if i < len(d_bearing) else None,
                    "native_precipitation": d_precip[i] if i < len(d_precip) else None,
                    "precipitation_probability": d_precip_prob[i] if i < len(d_precip_prob) else None,
                })

        return weather


def _m_to_km(value: float | None) -> float | None:
    """Convert visibility from metres to kilometres."""
    return round(value / 1000, 1) if value is not None else None
