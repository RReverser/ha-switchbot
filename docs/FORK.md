# Fork maintenance: tracking upstream

This integration (`switchbot_enhanced`) is a fork of Home Assistant core's
`switchbot` integration, slimmed to Meter Pro / Meter Pro CO2. The BLE
library comes from the `meter-pro-co2-weather-unset` branch of
`RReverser/pySwitchbot`, which is `mathismueller/pySwitchbot`'s
`feature/meter-pro-co2` branch (itself branched from `sblibs/pySwitchbot`)
plus a fix for the unset weather icon.
Upstream moves on both sides, so this file records where we stand and how
to pull upstream work in.

## Last synced state

| Upstream | State |
| --- | --- |
| `homeassistant/core` `switchbot/` component | Reviewed through `12f6a28` (2026-11-05). Ported: `None`-returning config entry methods, dropped `_set_confirm_only`. Already aligned: `connectivity`, `categories`, deferred-first-read polling, non-blocking migration, `ConfigType` import source, typed config entries. |
| `sblibs/pySwitchbot` (via our fork branch) | Fork branch includes everything through upstream `3.1.0` (`6d4feac`); zero upstream commits outstanding. Manifest pins `RReverser/pySwitchbot` commit `19580b0`. Upstream has **not** merged weather/threshold/calibration/external-MAC support, so the fork branch is still required. |

## Intentional divergences (do not "port back")

- Domain renamed `switchbot` → `switchbot_enhanced` (side-by-side with core).
- Only `METER_PRO` / `METER_PRO_CO2` supported; all other platforms, entity
  branches, services (`add_password`), translations, and icons removed.
- `async_migrate_entry` handles only `hygrometer_co2` → `METER_PRO_CO2`
  and never consults BLE (never blocks setup).
- `documentation` / `issue_tracker` point here, not at core docs.

Consequence for triage: upstream commits touching deleted files
(`climate.py`, `cover.py`, `lock.py`, …) or non-meter devices are
**auto-skip**. Only commits touching the shared core files below need
review: `__init__.py`, `config_flow.py`, `coordinator.py`, `entity.py`,
`manifest.json`, `sensor.py`, `binary_sensor.py`, `button.py`, `number.py`,
`select.py`, `switch.py`, `services.py`, `translations/en.json`.

## Sync SOP

Repeat for each side. The weekly `upstream-watch` workflow posts the
candidate lists into the tracking issue automatically; the steps below are
for acting on them.

### A. HA core component

```bash
# 1. List what's new since the last review (replace SHA with the newest
#    commit from the previous round):
gh api "repos/home-assistant/core/commits?path=homeassistant/components/switchbot&per_page=30" \
  -q '.[] | .sha[0:7] + " " + .commit.author.date + " " + (.commit.message | split("\n")[0])'
# 2. For anything touching a shared file, read the diff:
gh api repos/home-assistant/core/commits/<FULL_SHA> \
  --jq '.files[] | select(.filename | test("switchbot/(__init__|config_flow|coordinator|entity|manifest|sensor|binary_sensor|button|number|select|switch|services)")) | "#### " + .filename + "\n" + .patch'
# 3. Port by hand (cherry-pick does not apply: domain and scope differ),
#    run hassfest + HACS validation, note the new HEAD SHA here.
```

### B. pySwitchbot library (two hops: upstream → fork branch → manifest pin)

```bash
# 1. In the pySwitchbot clone, check what's new upstream:
git fetch upstream
git log --oneline <LAST_SYNCED_UPSTREAM_SHA>..upstream/main
# 2. Rebase the feature branch, run its pytest suite:
git checkout feature/meter-pro-co2
git rebase upstream/main
cd pySwitchbot && ../.venv/bin/pytest tests/test_meter_pro.py tests/test_meter_pro_weather.py
git push --force-with-lease
# 3. Pin the new fork commit in this repo's manifest.json
#    ("PySwitchbot@git+https://github.com/RReverser/pySwitchbot.git@<SHA>"),
#    update the SHA in the table above, push, and cut a release.
```

The manifest deliberately pins a **commit SHA**, not the branch: every
library change lands here as an explicit, reviewable bump instead of a
silent moving target.

## The long-term fix

If the Meter Pro enhancements ever land in core + upstream pySwitchbot,
this fork can be retired. Until then, keep the divergence small: prefer
additive changes in our files over restructuring shared logic, so future
upstream diffs still read cleanly.
