## Summary

Makes the integration installable via HACS and fixes several bugs found while using it with ECMWF models.

## HACS support
- `hacs.json`, `issue_tracker` and `codeowners` in the manifest (keys sorted as hassfest requires), a validation workflow, a LICENSE file, and README install steps.

## Bug fixes
- **11 invalid model identifiers** in `WEATHER_MODELS` (e.g. `ecmwf_ifs_9km` is now `ecmwf_ifs`) made setup fail with a 400 from the API. All identifiers are now checked against Open-Meteo's own model list.
- **Hourly forecast was hard-capped at 48 h** regardless of the "Forecast days" setting, which broke cards that build a multi-day view from hourly data. Hourly and daily lengths now follow `forecast_days`.
- **Sunrise/sunset sensors crashed on setup** (`'str' object has no attribute 'tzinfo'`). Timestamps are now parsed into timezone-aware datetimes.
- **Reconfigure showed empty fields** instead of saved values. The options flow now uses `add_suggested_values_to_schema`.

## Improvements
- Variable and model fields use tick-box and dropdown selectors with friendly labels instead of free text.
- Latitude/longitude default to the Home Assistant home location.
- New "Weather Model" diagnostic sensor, plus model attributes on the weather entity.

## Testing
Installed via HACS and run in Home Assistant with ECMWF IFS.

## Notes
- Version numbers in the manifest are from my fork's releases. Feel free to set your own.
- Happy to split this into smaller PRs if that's easier to review.
