# Open-Meteo Advanced — Home Assistant Integration

A custom integration for [Home Assistant](https://www.home-assistant.io/) that exposes the full power of the [Open-Meteo](https://open-meteo.com/) weather API: choose any forecasting model, select individual variables as sensors, and get a complete `weather` entity with hourly and daily forecasts.

> **Why not the official integration?**
> The built-in HA Open-Meteo integration covers a fixed set of variables and uses a single model. This integration lets you pick any combination of the 80+ available variables and any of the 48 supported models — including regional high-resolution models like ARPAE ICON-2I for Italy, Météo-France AROME, DWD ICON-D2, UKMO UK 2km, and many others.

---

## Features

- **48 weather models** — global (ECMWF, GFS, ICON, GEM, JMA, BOM, CMA…) and regional high-resolution (AROME France HD, ICON-D2, ICON-2I Italy, HARMONIE, UKMO UK 2km, MeteoSwiss, GeoSphere Austria…)
- **44 hourly sensor variables** — temperature, humidity, dew point, precipitation, radiation, evapotranspiration, soil temperature & moisture, CAPE, wind at multiple heights, visibility, and more
- **26 daily sensor variables** — max/min/mean temperature, precipitation sums, UV index, sunrise/sunset, sunshine duration, dominant wind…
- **15 current-condition sensor variables** — real-time values updated on every fetch
- **`weather` entity** with hourly (48 h) and daily (14 d) forecast — usable in the standard HA weather card and automations
- **Configurable update interval** (minimum 15 min), forecast window (1–16 days), and past-days lookback (0–92 days)
- Each sensor exposes a **`forecast` attribute** with the upcoming values (48 h for hourly, 14 d for daily)
- Fully reconfigurable after setup via the **Options flow**

---

## Requirements

- Home Assistant **2023.x or newer**
- Internet access to `api.open-meteo.com` (free, no API key required for personal use)

---

## Installation

### Manual

1. Download or clone this repository.
2. Copy the `custom_components/open_meteo_advanced/` folder into your HA configuration directory:
   ```
   <config>/custom_components/open_meteo_advanced/
   ```
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → + Add Integration** and search for **Open-Meteo Advanced**.

### HACS

This repository is not yet in the default HACS store, but you can add it as a **custom repository**:

1. In Home Assistant, go to **HACS → Integrations**.
2. Click the **⋮** menu (top right) → **Custom repositories**.
3. Add `https://github.com/m-l/ha-open-meteo-advanced` with category **Integration**.
4. Find **Open-Meteo Advanced** in HACS and click **Download**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & Services → + Add Integration** and search for **Open-Meteo Advanced**.

Or use this button (after adding the custom repository above):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=m-l&repository=ha-open-meteo-advanced&category=integration)

---

## Configuration

The integration is configured through a five-step UI wizard.

### Step 1 — Location & Model

| Field | Description |
|-------|-------------|
| **Location name** | Display name for the device (e.g. `Florence`) |
| **Latitude / Longitude** | Coordinates of the location to monitor |
| **Weather model** | One of 48 available models (see list below) |
| **Create weather entity** | Toggle to also create a `weather.*` entity |

### Step 2 — Timing

| Field | Default | Range |
|-------|---------|-------|
| **Update interval** | 60 min | 15 – 1440 min |
| **Forecast days** | 7 | 1 – 16 |
| **Past days to include** | 0 | 0 – 92 |

### Steps 3–5 — Variables

Enter variable names separated by commas. Leaving a field blank creates no sensors for that category.

- **Step 3** — Current variables (real-time)
- **Step 4** — Hourly variables
- **Step 5** — Daily variables

All settings can be changed at any time via **Settings → Devices & Services → Open-Meteo Advanced → Configure**.

---

## Available Variables

### Current
`temperature_2m` · `relative_humidity_2m` · `apparent_temperature` · `precipitation` · `rain` · `showers` · `snowfall` · `weather_code` · `cloud_cover` · `pressure_msl` · `surface_pressure` · `wind_speed_10m` · `wind_direction_10m` · `wind_gusts_10m` · `is_day`

### Hourly (selection)
`temperature_2m` · `dew_point_2m` · `apparent_temperature` · `relative_humidity_2m` · `precipitation` · `rain` · `showers` · `snowfall` · `snow_depth` · `precipitation_probability` · `weather_code` · `pressure_msl` · `surface_pressure` · `cloud_cover` · `cloud_cover_low` · `cloud_cover_mid` · `cloud_cover_high` · `wind_speed_10m/80m/120m/180m` · `wind_direction_10m/80m/120m/180m` · `wind_gusts_10m` · `shortwave_radiation` · `direct_radiation` · `direct_normal_irradiance` · `diffuse_radiation` · `global_tilted_irradiance` · `vapour_pressure_deficit` · `cape` · `evapotranspiration` · `et0_fao_evapotranspiration` · `freezing_level_height` · `visibility` · `soil_temperature_0/6/18/54cm` · `soil_moisture_0-1/1-3/3-9/9-27/27-81cm` · `is_day`

### Daily (selection)
`temperature_2m_max/mean/min` · `apparent_temperature_max/mean/min` · `precipitation_sum` · `rain_sum` · `showers_sum` · `snowfall_sum` · `precipitation_hours` · `precipitation_probability_max/mean/min` · `et0_fao_evapotranspiration` · `weather_code` · `sunrise` · `sunset` · `sunshine_duration` · `daylight_duration` · `wind_speed_10m_max` · `wind_gusts_10m_max` · `wind_direction_10m_dominant` · `shortwave_radiation_sum` · `uv_index_max` · `uv_index_clear_sky_max`

---

## Supported Weather Models

| Model | Coverage |
|-------|----------|
| `best_match` | Auto-selected best model for the location |
| `ecmwf_ifs_9km` / `ecmwf_ifs_025` | ECMWF IFS global |
| `ecmwf_aifs_025` | ECMWF AI-based forecast |
| `ncep_gfs_seamless` / `ncep_gfs_011` | NOAA GFS global |
| `ncep_hrrr_conus` | NOAA HRRR (USA high-res) |
| `ncep_gfs_graphcast` / `ncep_aigfs_025` | NOAA AI-based |
| `dwd_icon_seamless` / `dwd_icon_global` | DWD ICON global |
| `dwd_icon_eu` / `dwd_icon_d2` | DWD ICON Europe / Germany |
| `meteofrance_seamless` | Météo-France auto |
| `meteofrance_arpege_world` / `_europe` | Météo-France ARPEGE |
| `meteofrance_arome_france` / `_hd` | Météo-France AROME (high-res France) |
| `italia_meteo_arpae_icon_2i` | ARPAE ICON-2I (Italy 2 km) |
| `knmi_harmonie_arome_europe` / `_netherlands` | KNMI HARMONIE-AROME |
| `dmi_harmonie_arome_europe` | DMI HARMONIE-AROME |
| `metno_nordic_seamless` / `metno_nordic` | MET Norway Nordic |
| `ukmo_seamless` / `ukmo_global_10km` / `ukmo_uk_2km` | UK Met Office |
| `meteoswiss_seamless` / `_icon_ch1` / `_icon_ch2` | MeteoSwiss |
| `geosphere_seamless` / `geosphere_arome_austria` | GeoSphere Austria |
| `gem_seamless` / `gem_global` / `gem_regional` / `gem_hrdps_continental` | Environment Canada |
| `jma_seamless` / `jma_msm` / `jma_gsm` | JMA (Japan) |
| `kma_seamless` / `kma_ldps` / `kma_gdps` | KMA (Korea) |
| `bom_access_global` | BOM (Australia) |
| `cma_grapes_global` | CMA GRAPES (China) |

---

## Sensor Attributes

Every sensor exposes its upcoming values as a `forecast` attribute — useful in templates and automations.

**Hourly sensors** — next 48 hours:
```yaml
forecast:
  - time: "2026-05-12T15:00"
    value: 22.4
  - time: "2026-05-12T16:00"
    value: 23.1
  ...
```

**Daily sensors** — next 14 days:
```yaml
forecast:
  - time: "2026-05-12"
    value: 18.3
  - time: "2026-05-13"
    value: 21.0
  ...
```

---

## Weather Entity

When enabled, a `weather.<location_name>` entity is created. It supports:

- Current condition, temperature, humidity, pressure, wind, visibility, cloud cover
- **Hourly forecast** (48 h) — condition, temperature, wind, precipitation probability, precipitation, pressure, cloud cover, humidity
- **Daily forecast** (14 d) — condition, max/min temperature, dominant wind, precipitation sum, precipitation probability

The weather card in HA Lovelace will automatically show forecasts.

The required API variables for the weather entity are fetched **automatically** — no manual variable selection needed. If you also select those same variables as sensors, they are deduplicated into a single API call.

### WMO Code → HA Condition Mapping

| WMO | HA condition |
|-----|-------------|
| 0, 1 | `sunny` / `clear-night` |
| 2 | `partlycloudy` |
| 3 | `cloudy` |
| 45, 48 | `fog` |
| 51–55, 61–63, 80–81 | `rainy` |
| 56–57, 66–67 | `snowy-rainy` |
| 65, 82 | `pouring` |
| 71–77, 85–86 | `snowy` |
| 95 | `lightning` |
| 96, 99 | `hail` |

---

## Data Source

All weather data is fetched from the [Open-Meteo API](https://open-meteo.com/en/docs). The service is **free for non-commercial personal use** and does not require an API key.

---

## License

MIT
