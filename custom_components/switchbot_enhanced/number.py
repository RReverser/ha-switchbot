"""Number platform for SwitchBot Meter Pro devices."""

from datetime import timedelta
import logging
from typing import override

import switchbot
from switchbot.devices.meter_pro import MAX_TIME_OFFSET

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
PARTS_PER_MILLION: str = "ppm"

from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SwitchbotConfigEntry, SwitchbotDataUpdateCoordinator
from .entity import SwitchbotConnectionPolledEntity, exception_handler

PARALLEL_UPDATES = 0
SCAN_INTERVAL = timedelta(days=7)
_LOGGER = logging.getLogger(__name__)
_SECONDS_IN_MINUTE = 60
_MAX_TIME_OFFSET_MINUTES = MAX_TIME_OFFSET // _SECONDS_IN_MINUTE


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwitchbotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SwitchBot number platform."""
    coordinator = entry.runtime_data

    if isinstance(coordinator.device, switchbot.SwitchbotMeterPro):
        entities: list[NumberEntity] = [
            SwitchBotMeterProComfortColdNumber(coordinator),
            SwitchBotMeterProComfortHotNumber(coordinator),
            SwitchBotMeterProComfortDryNumber(coordinator),
            SwitchBotMeterProComfortWetNumber(coordinator),
            SwitchBotMeterProTemperatureOffsetNumber(coordinator),
            SwitchBotMeterProHumidityOffsetNumber(coordinator),
        ]
        if isinstance(coordinator.device, switchbot.SwitchbotMeterProCO2):
            entities.extend(
                [
                    SwitchBotMeterProCO2DisplayTimeOffsetNumber(coordinator),
                    SwitchBotMeterProCO2ThresholdGoodNumber(coordinator),
                    SwitchBotMeterProCO2ThresholdModerateNumber(coordinator),
                    SwitchBotMeterProCO2WeatherTemperatureNumber(coordinator),
                    SwitchBotMeterProCO2WeatherHumidityNumber(coordinator),
                ]
            )
        async_add_entities(entities)


class SwitchBotMeterProCO2DisplayTimeOffsetNumber(
    SwitchbotConnectionPolledEntity, NumberEntity
):
    """Number entity to set the time offset for Meter Pro CO2 devices."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "display_time_offset"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = -_MAX_TIME_OFFSET_MINUTES
    _attr_native_max_value = _MAX_TIME_OFFSET_MINUTES
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_display_time_offset"

    @exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set the time offset."""
        _LOGGER.debug("Setting time offset to %s minutes for %s", value, self._address)
        offset_minutes = round(value)
        offset_seconds = offset_minutes * _SECONDS_IN_MINUTE
        await self._device.set_time_offset(offset_seconds)
        self._attr_native_value = offset_minutes
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Fetch the latest time offset from the device."""
        offset_seconds = await self._device.get_time_offset()
        self._attr_native_value = round(offset_seconds / _SECONDS_IN_MINUTE)


class SwitchBotMeterProComfortColdNumber(SwitchbotConnectionPolledEntity, NumberEntity):
    """Comfort Cold temperature threshold."""

    _device: switchbot.SwitchbotMeterPro
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "comfort_cold"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = -20.0
    _attr_native_max_value = 79.5
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize comfort cold threshold number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_comfort_cold"
        self._attr_native_value = 18.0

    @exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set comfort cold threshold."""
        await self._device.set_comfortlevel(
            cold=value, hot=26.0, dry=30, wet=70
        )
        self._attr_native_value = value
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Keep native value."""
        if self._attr_native_value is None:
            self._attr_native_value = 18.0


class SwitchBotMeterProComfortHotNumber(SwitchbotConnectionPolledEntity, NumberEntity):
    """Comfort Hot temperature threshold."""

    _device: switchbot.SwitchbotMeterPro
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "comfort_hot"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = -19.5
    _attr_native_max_value = 80.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize comfort hot threshold number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_comfort_hot"
        self._attr_native_value = 26.0

    @exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set comfort hot threshold."""
        await self._device.set_comfortlevel(
            cold=18.0, hot=value, dry=30, wet=70
        )
        self._attr_native_value = value
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Keep native value."""
        if self._attr_native_value is None:
            self._attr_native_value = 26.0


class SwitchBotMeterProComfortDryNumber(SwitchbotConnectionPolledEntity, NumberEntity):
    """Comfort Dry relative humidity threshold."""

    _device: switchbot.SwitchbotMeterPro
    _attr_device_class = NumberDeviceClass.HUMIDITY
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "comfort_dry"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 1
    _attr_native_max_value = 98
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize comfort dry threshold number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_comfort_dry"
        self._attr_native_value = 30

    @exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set comfort dry threshold."""
        await self._device.set_comfortlevel(
            cold=18.0, hot=26.0, dry=int(value), wet=70
        )
        self._attr_native_value = int(value)
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Keep native value."""
        if self._attr_native_value is None:
            self._attr_native_value = 30


class SwitchBotMeterProComfortWetNumber(SwitchbotConnectionPolledEntity, NumberEntity):
    """Comfort Wet relative humidity threshold."""

    _device: switchbot.SwitchbotMeterPro
    _attr_device_class = NumberDeviceClass.HUMIDITY
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "comfort_wet"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 2
    _attr_native_max_value = 99
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize comfort wet threshold number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_comfort_wet"
        self._attr_native_value = 70

    @exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set comfort wet threshold."""
        await self._device.set_comfortlevel(
            cold=18.0, hot=26.0, dry=30, wet=int(value)
        )
        self._attr_native_value = int(value)
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Keep native value."""
        if self._attr_native_value is None:
            self._attr_native_value = 70


class SwitchBotMeterProTemperatureOffsetNumber(
    SwitchbotConnectionPolledEntity, NumberEntity
):
    """Temperature calibration offset."""

    _device: switchbot.SwitchbotMeterPro
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "temperature_offset"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = -10.0
    _attr_native_max_value = 10.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize temperature offset number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_temperature_offset"
        self._attr_native_value = 0.0

    @exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set temperature offset."""
        current_offsets = await self._device.get_temperature_humidity_offsets()
        hum = current_offsets.get("humidity_offset", 0)
        await self._device.set_temperature_humidity_offsets(
            temperature_offset=value, humidity_offset=hum
        )
        self._attr_native_value = value
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Fetch calibration offsets."""
        offsets = await self._device.get_temperature_humidity_offsets()
        self._attr_native_value = offsets["temperature_offset"]


class SwitchBotMeterProHumidityOffsetNumber(
    SwitchbotConnectionPolledEntity, NumberEntity
):
    """Humidity calibration offset."""

    _device: switchbot.SwitchbotMeterPro
    _attr_device_class = NumberDeviceClass.HUMIDITY
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "humidity_offset"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = -30
    _attr_native_max_value = 30
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize humidity offset number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_humidity_offset"
        self._attr_native_value = 0

    @exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set humidity offset."""
        current_offsets = await self._device.get_temperature_humidity_offsets()
        temp = current_offsets.get("temperature_offset", 0.0)
        await self._device.set_temperature_humidity_offsets(
            temperature_offset=temp, humidity_offset=int(value)
        )
        self._attr_native_value = int(value)
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Fetch calibration offsets."""
        offsets = await self._device.get_temperature_humidity_offsets()
        self._attr_native_value = offsets["humidity_offset"]


class SwitchBotMeterProCO2ThresholdGoodNumber(
    SwitchbotConnectionPolledEntity, NumberEntity
):
    """CO2 Good Air Quality threshold (Green boundary)."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "co2_threshold_good"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 500
    _attr_native_max_value = 1800
    _attr_native_step = 100
    _attr_native_unit_of_measurement = PARTS_PER_MILLION
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize CO2 good threshold number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_co2_threshold_good"
        self._attr_native_value = 1000

    @exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set CO2 good threshold."""
        moderate = getattr(self._device, "_co2_threshold_moderate", 1400)
        await self._device.set_co2_thresholds(
            lower=int(value), upper=moderate
        )
        self._device._co2_threshold_good = int(value)
        self._attr_native_value = int(value)
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Keep native value."""
        if self._attr_native_value is None:
            self._attr_native_value = 1000


class SwitchBotMeterProCO2ThresholdModerateNumber(
    SwitchbotConnectionPolledEntity, NumberEntity
):
    """CO2 Moderate Air Quality threshold (Orange/Red boundary)."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "co2_threshold_moderate"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 600
    _attr_native_max_value = 1900
    _attr_native_step = 100
    _attr_native_unit_of_measurement = PARTS_PER_MILLION
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize CO2 moderate threshold number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_co2_threshold_moderate"
        self._attr_native_value = 1400

    @exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set CO2 moderate threshold."""
        good = getattr(self._device, "_co2_threshold_good", 1000)
        await self._device.set_co2_thresholds(
            lower=good, upper=int(value)
        )
        self._device._co2_threshold_moderate = int(value)
        self._attr_native_value = int(value)
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Keep native value."""
        if self._attr_native_value is None:
            self._attr_native_value = 1400


class SwitchBotMeterProCO2WeatherTemperatureNumber(
    SwitchbotConnectionPolledEntity, NumberEntity
):
    """Outdoor (weather) temperature stored on Meter Pro CO2."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "weather_temperature"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = -127.9
    _attr_native_max_value = 127.9
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the weather temperature number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_weather_temperature"

    @exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set the displayed outdoor temperature."""
        await self._device.set_weather(temperature_c=value)
        self._attr_native_value = value
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Fetch the displayed outdoor temperature."""
        weather = await self._device.get_weather()
        self._attr_native_value = weather["temperature_c"]


class SwitchBotMeterProCO2WeatherHumidityNumber(
    SwitchbotConnectionPolledEntity, NumberEntity
):
    """Outdoor (weather) humidity stored on Meter Pro CO2."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_device_class = NumberDeviceClass.HUMIDITY
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "weather_humidity"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 1
    _attr_native_max_value = 99
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the weather humidity number."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_weather_humidity"

    @exception_handler
    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set the displayed outdoor humidity."""
        await self._device.set_weather(humidity=value)
        self._attr_native_value = int(value)
        self.async_write_ha_state()

    @override
    async def _async_read_value(self) -> None:
        """Fetch the displayed outdoor humidity."""
        weather = await self._device.get_weather()
        self._attr_native_value = weather["humidity"]
