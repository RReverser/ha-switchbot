# SwitchBot Meter Pro (Enhanced) for Home Assistant

[![Marketplace](https://img.shields.io/badge/Marketplace-Custom-orange.svg)](https://contributors.home-assistant.io/marketplace/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.11.0%2B-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

<!-- ha-marketplace:exclude-start -->

> [!NOTE]
> Runs side-by-side with the built-in `switchbot` integration under its own
> domain `switchbot_enhanced`. No replacement confirmation, and eligible for
> the default Marketplace catalog. You can keep core for other devices and
> use this for Meter Pro / Meter Pro CO2 — or move everything over.

[![Open your Home Assistant instance and open a repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=mathismueller&repository=ha-switchbot&category=integration)

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=switchbot_enhanced)

<!-- ha-marketplace:exclude-end -->

## Disclaimer

This project was implemented in large parts with the use of coding agents and has not been fully reviewed. 

SwitchBot, Inc. is not affiliated with this project and does not provide support for it. Use at your own risk.

## Features

An enhanced custom component for the **SwitchBot Meter Pro** (`WoTHP`) and **SwitchBot Meter Pro CO2** (`WoTHPc`), featuring complete reverse-engineered control and entity support. Limited testing was performed on the `WoTHPc` variant.

Runs side-by-side with the core Home Assistant `switchbot` integration under its own domain `switchbot_enhanced` — it only handles Meter Pro / Meter Pro CO2. All other SwitchBot devices stay on the core integration. Add Meter Pro devices here at your own pace. Works natively through **ESPHome Active Bluetooth Proxies** and local Bluetooth adapters.

---

## Full List of Enhancements for Meter Pro & Meter Pro CO2

### 1. Switches (`switch`)
* **Battery Indicator Glyph (`switch.battery_indicator`)**: Toggle whether the physical battery gauge icon appears on the physical LCD display.
* **Outdoor Sensor Display (`switch.display_data_source`)**: Toggle between Indoor ("IN") and Outdoor ("OUT") sensor display modes on the LCD screen.
* **Toggle ℃ / ℉ on Button (`switch.button_toggle_unit`)**: Enable or disable switching temperature unit when pressing the top physical button.
* **Toggle Data Source on Button (`switch.button_toggle_data_source`)**: Enable or disable switching indoor/outdoor data source when pressing the top physical button.
* **Buzzer Alarm Sound (`switch.buzzer_sound`)**: Toggle between audible buzzer alarm and silent screen flashing when environmental thresholds are breached.

### 2. Selects (`select`)
* **Time Display Format (`select.time_format`)**: Switch between `12h` (AM/PM) and `24h` clock modes.
* **Date Display Format (`select.date_format`)**: Switch between Month/Day (`MM/DD`) and Day/Month (`DD/MM`).
* **Weather Condition Icon (`select.weather_condition`)**: Select the weather forecast icon displayed on the LCD screen (`sunny`, `partly_cloudy`, `cloudy`, `rainy`, `pouring`, `snowy`, `heavy_snow`, `none`; disabled by default).
* **Buzzer Volume (`select.buzzer_volume`)**: Set alarm volume (`Low`, `Medium`, `High`).
* **CO2 Measurement Interval (`select.co2_update_interval`)**: Configure background sampling interval (`5m`, `10m`, `30m`).

### 3. Numbers (`number`)
* **Comfort Temperature Thresholds**:
  * `number.comfort_cold`: Lower temperature threshold for `COMFORT` status (°C, 0.5°C step).
  * `number.comfort_hot`: Upper temperature threshold for `COMFORT` status (°C, 0.5°C step).
* **Comfort Humidity Thresholds**:
  * `number.comfort_dry`: Lower humidity threshold before display segments show `DRY` (%).
  * `number.comfort_wet`: Upper humidity threshold before display segments show `WET` (%).
* **Weather Temperature / Humidity (`number.weather_temperature`, `number.weather_humidity`)**: Outdoor (weather) temperature and humidity stored on the Meter Pro CO2 (disabled by default). The meter only shows them when its temperature and humidity source is set to local weather, which this integration cannot set yet; the "Outdoor sensor display" switch only changes the IN/OUT icon.
* **CO2 Air Quality Thresholds**:
  * `number.co2_threshold_good`: Boundary between Good (Green) and Moderate (Orange) air quality (ppm).
  * `number.co2_threshold_moderate`: Boundary between Moderate (Orange) and Poor (Red) air quality (ppm).
* **Sensor Calibration Offsets**:
  * `number.temperature_offset`: Hardware temperature calibration offset (-10.0 to +10.0 °C).
  * `number.humidity_offset`: Hardware relative humidity calibration offset (-30 to +30 %).
* **Time Display Offset (`number.display_time_offset`)**: Adjust local time display offset.

### 4. Buttons (`button`)
* **Sync Date and Time (`button.sync_datetime`)**: Immediately synchronize the hardware real-time clock to Home Assistant UTC time.
* **Refresh Temperature & Humidity (`button.refresh_measurements`)**: Immediately trigger an environmental sensor (temperature and humidity) measurement refresh on the hardware (simulates top button press; does not perform CO2 sampling).
* **Force CO2 Measurement (`button.force_co2_measurement`)**: Trigger an immediate, fresh NDIR CO2 sensor measurement regardless of the sleep interval, polling the result and updating Home Assistant sensor state.
* **Silence Alarm (`button.silence_alarm`)**: Mute the active alarm buzzer sound and stop screen flashing.
* **Calibrate CO2 Sensor (`button.calibrate_co2`)**: Start the 5-minute automated CO2 sensor recalibration routine (place device in ventilated outdoor air first).

### 5. Diagnostic Sensors (`sensor` & `binary_sensor`)
* **Firmware Version (`sensor.firmware`)**: Diagnostic sensor displaying the device firmware version (e.g. `1.5`), polled and cached from device basic info.
* **USB-C Power Status (`binary_sensor.usb_c_status`)**: Diagnostic binary sensor indicating whether the Meter Pro CO2 is connected to USB-C constant power (`Connected` / `Disconnected`), updated in real time via broadcast advertisements and GATT connection.

### 6. Actions / Services (`service`)
* **`switchbot_enhanced.meter_pro_set_weather`**: Push the weather forecast icon, outdoor temperature (°C) and/or outdoor humidity (%) to the Meter Pro CO2. The icon shows in the LCD header; the temperature and humidity are stored but not shown (see above). Omitted fields keep their current values.
  ```yaml
  action: switchbot_enhanced.meter_pro_set_weather
  data:
    device_id: YOUR_METER_PRO_DEVICE_ID
    icon: rainy # Options: sunny, partly_cloudy, cloudy, rainy, pouring, heavy_rain, snowy, light_snow, heavy_snow, none
    temperature: 8.5 # -127.9..127.9
    humidity: 82 # 1..99
  ```
* **`switchbot_enhanced.meter_pro_set_external_sensor_mac`**: Pair an external sensor MAC address (e.g. SwitchBot Outdoor Meter or emulated ESP32 beacon) to the Meter Pro hardware display. See the [ESPHome External Sensor Emulation](#external--outdoor-sensor-emulation-via-esphome) section below for details.
  ```yaml
  action: switchbot_enhanced.meter_pro_set_external_sensor_mac
  data:
    device_id: YOUR_METER_PRO_DEVICE_ID
    mac_address: "AA:BB:CC:DD:EE:FF" # Or "00:00:00:00:00:00" to clear
    slot: 1 # Optional: 1 (primary display) or 2 (secondary)
    switch_display: true # Optional (default: true): automatically switches screen to OUT on pair, or IN on clear
  ```

---

## Installation

Requires Home Assistant 2026.11.0 or newer (see `hacs.json`).

<!-- ha-marketplace:exclude-start -->

### Via Marketplace (Recommended)

1. Open Home Assistant → **Settings** → **Marketplace**.
2. Click the menu → **Custom repositories**.
3. Add this repository URL (`https://github.com/mathismueller/ha-switchbot`), category: **Integration**.
4. Click **Install**, then restart Home Assistant when prompted.
   First installs with a config flow load right away; updates/removals need a restart.

> On Home Assistant 2026.10 or older, use **HACS** → **Integrations** →
> **Custom repositories** instead. The standalone HACS installer does not work
> on 2026.11+.

### Manual Installation
1. Copy the `custom_components/switchbot_enhanced/` folder into your Home Assistant configuration directory (`<config_dir>/custom_components/switchbot_enhanced/`).
2. Restart Home Assistant.

<!-- ha-marketplace:exclude-end -->

> [!NOTE]
> Domain is `switchbot_enhanced`, so it installs alongside core `switchbot`
> with no replacement prompt and no re-pairing of core devices needed.
> Bluetooth discovery will show Meter Pro devices in both integrations —
> add them under **SwitchBot Bluetooth (Enhanced)** and ignore (or disable)
> the duplicate core discovery if you only want them here.

---

## External / Outdoor Sensor Emulation via ESPHome

The SwitchBot Meter Pro (and CO2) can display outdoor temperature and humidity readings received directly from an external SwitchBot Outdoor Meter via local BLE broadcasts (`0x0969` / `WoSensorTH`).

If you do not own a physical SwitchBot Outdoor Meter, **you can emulate one using any ESP32 running ESPHome** (alongside an ESPHome BLE Proxy on the same device). This allows you to broadcast any Home Assistant temperature and humidity entities as SwitchBot Outdoor Meter advertisement beacons.:

1. **Flash ESPHome**: Use the provided [ESPHome SwitchBot Beacon Template](examples/esphome_switchbot_outdoor_meter.yaml). It subscribes to any Home Assistant temperature and humidity entities and broadcasts them as SwitchBot Outdoor Meter advertisement beacons using your ESP32's BLE MAC address.
2. **Pair the MAC Address**: Call the `switchbot_enhanced.meter_pro_set_external_sensor_mac` action in Home Assistant with your ESP32's Bluetooth MAC address (Slot 1). The display will automatically switch from `IN` to `OUT` as instant visual confirmation!
3. **Control Display Source**: You can toggle between internal sensor readings (`IN`) and external readings (`OUT`) programmatically via the `switch.display_data_source` entity, or physically by pressing the top hardware button (configurable via `switch.button_toggle_data_source`).

> [!NOTE]
> When `switch.button_toggle_data_source` is enabled, pressing the physical top button changes the live display in RAM. However, the hardware firmware enforces its persistent profile (`070103`) whenever button settings are written. To permanently switch the screen back to internal readings, turn off `switch.display_data_source` or clear the MAC pairing.

## Acknowledgments & Credits

This project builds directly upon the foundational work of the Home Assistant and SwitchBot open-source communities:

* **[Home Assistant Core](https://github.com/home-assistant/core)**:
  This custom component is derived from the official `switchbot` core integration. Huge credit to the original integration authors and code owners:
  * Daniel Hjelseth Høyer ([@danielhiversen](https://github.com/danielhiversen))
  * [@RenierM26](https://github.com/RenierM26)
  * [@murtas](https://github.com/murtas)
  * [@Eloston](https://github.com/Eloston)
  * [@dsypniewski](https://github.com/dsypniewski)
  * [@zerzhang](https://github.com/zerzhang)
  * And all Home Assistant contributors.

* **[pySwitchbot](https://github.com/sblibs/pySwitchbot)**:
  All low-level BLE communication, packet parsing, and GATT command execution rely on `pySwitchbot`, originally authored by Daniel Hjelseth Høyer. Our Meter Pro and Meter Pro CO2 protocol implementations extend this library directly. 

  The extension is based on the following community pull requests that were not yet merged into the main `pySwitchbot` repository: 
  * [Issue #581](https://github.com/sblibs/pySwitchbot/issues/581) by [@meuxx](https://github.com/meuxx) implementing the weather icon functionality.
  
  * [Issue #559](https://github.com/sblibs/pySwitchbot/pull/559) and [Issue #430](https://github.com/sblibs/pySwitchbot/pull/430) by [@ahrmn](https://github.com/ahrmn) implementing most of the Meter Pro and Meter Pro CO2 functionality, including the calibration, the buzzer, comfort thresholds, and more. 

---

## 📄 License

This project is licensed under the **Apache License 2.0** — in continuity with Home Assistant Core. See the [LICENSE](LICENSE) file for complete details.
