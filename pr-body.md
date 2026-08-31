## Summary

Adds the files required for this integration to be installable via [HACS](https://hacs.xyz/) as a custom repository, as a first step toward eventual inclusion in the default HACS store.

## Changes

- **`hacs.json`** (new) — repository manifest HACS needs to recognize this as a valid integration repo.
- **`custom_components/open_meteo_advanced/manifest.json`** — added `issue_tracker` and populated `codeowners`, both required by HACS validation but previously missing/empty. Also pointed `documentation` at this repo instead of the generic Open-Meteo API docs.
- **`.github/workflows/validate.yml`** (new) — runs `hassfest` and `hacs/action` validation on push/PR, matching HACS's own integration template.
- **`LICENSE`** (new, MIT) — the README already stated "License: MIT" but no LICENSE file existed.
- **`README.md`** — replaced the "HACS (coming soon)" placeholder with real custom-repository install steps and a My Home Assistant install button.

## Testing

Installed and verified working via HACS as a custom repository (`https://github.com/m-l/ha-open-meteo-advanced`) pointed at this branch.

## Notes for the maintainer

- `codeowners` currently lists `@stilli00` and `@m-l` — happy to adjust if you'd prefer just yourself, or want me added differently.
- CI validation ignores the `brands` check for now, since no brand icon exists yet (`custom_components/open_meteo_advanced/brand/`). Can follow up with that separately if useful — it's a bit more involved since brand assets for HACS-only (non-core) integrations live in the integration's own `brand/` folder rather than the `home-assistant/brands` repo.
