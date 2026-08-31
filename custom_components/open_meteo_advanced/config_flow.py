"""Config flow for Open-Meteo Advanced."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CURRENT_VARS,
    CONF_DAILY_VARS,
    CONF_FORECAST_DAYS,
    CONF_HOURLY_VARS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MODEL,
    CONF_NAME,
    CONF_PAST_DAYS,
    CONF_UPDATE_INTERVAL,
    CONF_WEATHER_ENTITY,
    CURRENT_VARIABLES,
    DAILY_VARIABLES,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_NAME,
    DEFAULT_PAST_DAYS,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    HOURLY_VARIABLES,
    VariableMeta,
    WEATHER_MODELS,
)

_LOGGER = logging.getLogger(__name__)


def _variable_options(variables: dict[str, VariableMeta]) -> list[selector.SelectOptionDict]:
    """Build checkbox options with friendly labels from a variable metadata dict."""
    return [
        selector.SelectOptionDict(value=key, label=meta.name)
        for key, meta in variables.items()
    ]


def _variable_selector(variables: dict[str, VariableMeta]) -> selector.SelectSelector:
    """A tick-box multi-select for choosing weather variables, labeled not raw keys."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=_variable_options(variables),
            multiple=True,
            mode=selector.SelectSelectorMode.LIST,
            sort=True,
        )
    )


_MODEL_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[
            selector.SelectOptionDict(value=key, label=label)
            for key, label in WEATHER_MODELS.items()
        ],
        multiple=False,
        mode=selector.SelectSelectorMode.DROPDOWN,
    )
)


class OpenMeteoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Multi-step config flow for Open-Meteo Advanced."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_timing()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_LATITUDE, default=self.hass.config.latitude): vol.Coerce(float),
                vol.Required(CONF_LONGITUDE, default=self.hass.config.longitude): vol.Coerce(float),
                vol.Required(CONF_MODEL, default="best_match"): _MODEL_SELECTOR,
                vol.Required(CONF_WEATHER_ENTITY, default=True): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_timing(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        if user_input is not None:
            self._data[CONF_UPDATE_INTERVAL] = int(user_input[CONF_UPDATE_INTERVAL])
            self._data[CONF_FORECAST_DAYS] = int(user_input[CONF_FORECAST_DAYS])
            self._data[CONF_PAST_DAYS] = int(user_input[CONF_PAST_DAYS])
            return await self.async_step_current_vars()

        schema = vol.Schema(
            {
                vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=15, max=1440)
                ),
                vol.Required(CONF_FORECAST_DAYS, default=DEFAULT_FORECAST_DAYS): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=16)
                ),
                vol.Required(CONF_PAST_DAYS, default=DEFAULT_PAST_DAYS): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=92)
                ),
            }
        )
        return self.async_show_form(step_id="timing", data_schema=schema)

    async def async_step_current_vars(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        if user_input is not None:
            self._data[CONF_CURRENT_VARS] = user_input.get(CONF_CURRENT_VARS, [])
            return await self.async_step_hourly_vars()

        schema = vol.Schema(
            {
                vol.Optional(CONF_CURRENT_VARS, default=[]): _variable_selector(CURRENT_VARIABLES),
            }
        )
        return self.async_show_form(step_id="current_vars", data_schema=schema)

    async def async_step_hourly_vars(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        if user_input is not None:
            self._data[CONF_HOURLY_VARS] = user_input.get(CONF_HOURLY_VARS, [])
            return await self.async_step_daily_vars()

        schema = vol.Schema(
            {
                vol.Optional(CONF_HOURLY_VARS, default=[]): _variable_selector(HOURLY_VARIABLES),
            }
        )
        return self.async_show_form(step_id="hourly_vars", data_schema=schema)

    async def async_step_daily_vars(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        if user_input is not None:
            self._data[CONF_DAILY_VARS] = user_input.get(CONF_DAILY_VARS, [])
            return self.async_create_entry(
                title=self._data.get(CONF_NAME, DEFAULT_NAME),
                data=self._data,
            )

        schema = vol.Schema(
            {
                vol.Optional(CONF_DAILY_VARS, default=[]): _variable_selector(DAILY_VARIABLES),
            }
        )
        return self.async_show_form(step_id="daily_vars", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "OpenMeteoOptionsFlow":
        return OpenMeteoOptionsFlow(config_entry)


class OpenMeteoOptionsFlow(config_entries.OptionsFlow):
    """Reconfigure all settings after initial setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._data: dict[str, Any] = {**config_entry.data, **config_entry.options}

    def _suggest(self, schema: vol.Schema, suggested: dict[str, Any]) -> vol.Schema:
        """Pre-fill a form with current values.

        Plain vol default= is not reliably shown for *saved* values in an
        options flow (home-assistant/frontend#22419) - add_suggested_values_to_schema
        is HA's documented fix. Falls back to the schema as-is on HA versions
        old enough not to have it.
        """
        try:
            return self.add_suggested_values_to_schema(schema, suggested)
        except AttributeError:
            return schema

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_timing()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_LATITUDE): vol.Coerce(float),
                vol.Required(CONF_LONGITUDE): vol.Coerce(float),
                vol.Required(CONF_MODEL): _MODEL_SELECTOR,
                vol.Required(CONF_WEATHER_ENTITY): bool,
            }
        )
        suggested = {
            CONF_NAME: self._data.get(CONF_NAME, DEFAULT_NAME),
            CONF_LATITUDE: self._data.get(CONF_LATITUDE, self.hass.config.latitude),
            CONF_LONGITUDE: self._data.get(CONF_LONGITUDE, self.hass.config.longitude),
            CONF_MODEL: self._data.get(CONF_MODEL, "best_match"),
            CONF_WEATHER_ENTITY: self._data.get(CONF_WEATHER_ENTITY, True),
        }
        return self.async_show_form(step_id="init", data_schema=self._suggest(schema, suggested))

    async def async_step_timing(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        if user_input is not None:
            self._data[CONF_UPDATE_INTERVAL] = int(user_input[CONF_UPDATE_INTERVAL])
            self._data[CONF_FORECAST_DAYS] = int(user_input[CONF_FORECAST_DAYS])
            self._data[CONF_PAST_DAYS] = int(user_input[CONF_PAST_DAYS])
            return await self.async_step_current_vars()

        schema = vol.Schema(
            {
                vol.Required(CONF_UPDATE_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=15, max=1440)),
                vol.Required(CONF_FORECAST_DAYS): vol.All(vol.Coerce(int), vol.Range(min=1, max=16)),
                vol.Required(CONF_PAST_DAYS): vol.All(vol.Coerce(int), vol.Range(min=0, max=92)),
            }
        )
        suggested = {
            CONF_UPDATE_INTERVAL: self._data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            CONF_FORECAST_DAYS: self._data.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS),
            CONF_PAST_DAYS: self._data.get(CONF_PAST_DAYS, DEFAULT_PAST_DAYS),
        }
        return self.async_show_form(step_id="timing", data_schema=self._suggest(schema, suggested))

    async def async_step_current_vars(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        if user_input is not None:
            self._data[CONF_CURRENT_VARS] = user_input.get(CONF_CURRENT_VARS, [])
            return await self.async_step_hourly_vars()

        schema = vol.Schema({vol.Optional(CONF_CURRENT_VARS): _variable_selector(CURRENT_VARIABLES)})
        suggested = {CONF_CURRENT_VARS: self._data.get(CONF_CURRENT_VARS, [])}
        return self.async_show_form(step_id="current_vars", data_schema=self._suggest(schema, suggested))

    async def async_step_hourly_vars(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        if user_input is not None:
            self._data[CONF_HOURLY_VARS] = user_input.get(CONF_HOURLY_VARS, [])
            return await self.async_step_daily_vars()

        schema = vol.Schema({vol.Optional(CONF_HOURLY_VARS): _variable_selector(HOURLY_VARIABLES)})
        suggested = {CONF_HOURLY_VARS: self._data.get(CONF_HOURLY_VARS, [])}
        return self.async_show_form(step_id="hourly_vars", data_schema=self._suggest(schema, suggested))

    async def async_step_daily_vars(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        if user_input is not None:
            self._data[CONF_DAILY_VARS] = user_input.get(CONF_DAILY_VARS, [])
            return self.async_create_entry(title="", data=self._data)

        schema = vol.Schema({vol.Optional(CONF_DAILY_VARS): _variable_selector(DAILY_VARIABLES)})
        suggested = {CONF_DAILY_VARS: self._data.get(CONF_DAILY_VARS, [])}
        return self.async_show_form(step_id="daily_vars", data_schema=self._suggest(schema, suggested))
