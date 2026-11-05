"""Select platform for SwitchBot Meter Pro."""

import contextlib
from datetime import timedelta
import logging
from typing import override

import switchbot
from switchbot import MeterProWeatherIcon

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SwitchbotConfigEntry, SwitchbotDataUpdateCoordinator
from .entity import SwitchbotConnectionPolledEntity, exception_handler

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0

SCAN_INTERVAL = timedelta(days=7)
TIME_FORMAT_12H = "12h"
TIME_FORMAT_24H = "24h"
TIME_FORMAT_OPTIONS = [TIME_FORMAT_12H, TIME_FORMAT_24H]

DATE_FORMAT_MM_DD = "mm_dd"
DATE_FORMAT_DD_MM = "dd_mm"
DATE_FORMAT_OPTIONS = [DATE_FORMAT_MM_DD, DATE_FORMAT_DD_MM]

BUZZER_VOL_LOW = "low"
BUZZER_VOL_MEDIUM = "medium"
BUZZER_VOL_HIGH = "high"
BUZZER_VOLUME_OPTIONS = [BUZZER_VOL_LOW, BUZZER_VOL_MEDIUM, BUZZER_VOL_HIGH]

INTERVAL_5M = "5m"
INTERVAL_10M = "10m"
INTERVAL_30M = "30m"
CO2_INTERVAL_OPTIONS = [INTERVAL_5M, INTERVAL_10M, INTERVAL_30M]

WEATHER_ICON_OPTIONS = [
    "none",
    "sunny",
    "partly_cloudy",
    "cloudy",
    "rainy",
    "pouring",
    "snowy",
    "heavy_snow",
]
WEATHER_OPTION_TO_ICON: dict[str, MeterProWeatherIcon] = {
    "none": MeterProWeatherIcon.NONE,
    "sunny": MeterProWeatherIcon.SUNNY,
    "partly_cloudy": MeterProWeatherIcon.PARTLY_CLOUDY,
    "cloudy": MeterProWeatherIcon.CLOUDY,
    "rainy": MeterProWeatherIcon.RAINY,
    "pouring": MeterProWeatherIcon.POURING,
    "snowy": MeterProWeatherIcon.SNOWY,
    "heavy_snow": MeterProWeatherIcon.HEAVY_SNOW,
}
WEATHER_ICON_TO_OPTION: dict[MeterProWeatherIcon, str] = {
    icon: option for option, icon in WEATHER_OPTION_TO_ICON.items()
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwitchbotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SwitchBot select platform."""
    coordinator = entry.runtime_data

    if isinstance(coordinator.device, switchbot.SwitchbotMeterPro):
        entities: list[SelectEntity] = [
            SwitchBotMeterProCO2TimeFormatSelect(coordinator),
            SwitchBotMeterProDateFormatSelect(coordinator),
            SwitchBotMeterProTemperatureUpdateIntervalSelect(coordinator),
            SwitchBotMeterProWeatherConditionSelect(coordinator),
        ]
        if isinstance(coordinator.device, switchbot.SwitchbotMeterProCO2):
            entities.extend(
                [
                    SwitchBotMeterProCO2BuzzerVolumeSelect(coordinator),
                    SwitchBotMeterProCO2UpdateIntervalSelect(coordinator),
                ]
            )
        async_add_entities(entities)


class SwitchBotMeterProCO2TimeFormatSelect(
    SwitchbotConnectionPolledEntity, SelectEntity
):
    """Select entity to set time display format on Meter Pro CO2."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "time_format"
    _attr_options = TIME_FORMAT_OPTIONS

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_time_format"

    @exception_handler
    @override
    async def async_select_option(self, option: str) -> None:
        """Change the time display format."""
        _LOGGER.debug("Setting time format to %s for %s", option, self._address)
        is_12h_mode = option == TIME_FORMAT_12H
        await self._device.set_time_display_format(is_12h_mode)
        self._attr_current_option = option
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Fetch the latest time format from the device."""
        device_time = await self._device.get_datetime()
        self._attr_current_option = (
            TIME_FORMAT_12H if device_time["12h_mode"] else TIME_FORMAT_24H
        )


class SwitchBotMeterProDateFormatSelect(SwitchbotConnectionPolledEntity, SelectEntity):
    """Select entity to set date display format on Meter Pro."""

    _device: switchbot.SwitchbotMeterPro
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "date_format"
    _attr_options = DATE_FORMAT_OPTIONS

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_date_format"

    @exception_handler
    @override
    async def async_select_option(self, option: str) -> None:
        """Change the date display format."""
        is_month_first = option == DATE_FORMAT_MM_DD
        await self._device.set_date_display_format(is_month_first)
        self._attr_current_option = option
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Default date format."""
        if self._attr_current_option is None:
            self._attr_current_option = DATE_FORMAT_MM_DD


class SwitchBotMeterProCO2BuzzerVolumeSelect(
    SwitchbotConnectionPolledEntity, SelectEntity
):
    """Select entity to set buzzer volume on Meter Pro CO2."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "buzzer_volume"
    _attr_options = BUZZER_VOLUME_OPTIONS

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_buzzer_volume"

    @exception_handler
    @override
    async def async_select_option(self, option: str) -> None:
        """Change the buzzer volume."""
        vol_map = {BUZZER_VOL_LOW: 2, BUZZER_VOL_MEDIUM: 3, BUZZER_VOL_HIGH: 4}
        await self._device.set_alert_sound(sound_on=True, volume=vol_map[option])
        self._attr_current_option = option
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Default buzzer volume."""
        if self._attr_current_option is None:
            self._attr_current_option = BUZZER_VOL_MEDIUM


class SwitchBotMeterProCO2UpdateIntervalSelect(
    SwitchbotConnectionPolledEntity, SelectEntity
):
    """Select entity to set CO2 update interval on Meter Pro CO2."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "co2_update_interval"
    _attr_options = CO2_INTERVAL_OPTIONS

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_co2_update_interval"

    @exception_handler
    @override
    async def async_select_option(self, option: str) -> None:
        """Change the CO2 measurement update interval."""
        sec_map = {INTERVAL_5M: 300, INTERVAL_10M: 600, INTERVAL_30M: 1800}
        await self._device.set_co2_update_interval(sec_map[option])
        self._attr_current_option = option
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Fetch active CO2 update interval."""
        sec = await self._device.get_co2_update_interval()
        if sec == 300:
            self._attr_current_option = INTERVAL_5M
        elif sec == 600:
            self._attr_current_option = INTERVAL_10M
        elif sec == 1800:
            self._attr_current_option = INTERVAL_30M


class SwitchBotMeterProTemperatureUpdateIntervalSelect(
    SwitchbotConnectionPolledEntity, SelectEntity
):
    """Select entity to set temperature and humidity update interval on Meter Pro."""

    _device: switchbot.SwitchbotMeterPro
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "temperature_update_interval"
    _attr_options = CO2_INTERVAL_OPTIONS

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_temperature_update_interval"

    @exception_handler
    @override
    async def async_select_option(self, option: str) -> None:
        """Change the temperature measurement update interval."""
        sec_map = {INTERVAL_5M: 300, INTERVAL_10M: 600, INTERVAL_30M: 1800}
        await self._device.set_temperature_update_interval(sec_map[option])
        self._attr_current_option = option
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Fetch active temperature update interval."""
        sec = await self._device.get_temperature_update_interval()
        if sec == 300:
            self._attr_current_option = INTERVAL_5M
        elif sec == 600:
            self._attr_current_option = INTERVAL_10M
        elif sec == 1800:
            self._attr_current_option = INTERVAL_30M


class SwitchBotMeterProWeatherConditionSelect(
    SwitchbotConnectionPolledEntity, SelectEntity
):
    """Select entity to set weather condition icon on Meter Pro."""

    _device: switchbot.SwitchbotMeterPro
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "weather_condition"
    _attr_options = WEATHER_ICON_OPTIONS
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the weather condition select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_weather_condition"

    @exception_handler
    @override
    async def async_select_option(self, option: str) -> None:
        """Change the displayed weather condition icon."""
        icon = WEATHER_OPTION_TO_ICON[option]
        await self._device.set_weather(icon=icon)
        self._attr_current_option = option
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Fetch active weather condition icon."""
        weather = await self._device.get_weather()
        if icon := weather.get("icon"):
            if isinstance(icon, MeterProWeatherIcon):
                self._attr_current_option = WEATHER_ICON_TO_OPTION.get(icon)
            elif isinstance(icon, int):
                with contextlib.suppress(ValueError):
                    self._attr_current_option = WEATHER_ICON_TO_OPTION.get(
                        MeterProWeatherIcon(icon)
                    )
