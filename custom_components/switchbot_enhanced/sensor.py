"""Support for SwitchBot Meter Pro sensors."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

import switchbot

from homeassistant.components.bluetooth import async_last_service_info
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfRatio,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SwitchbotConfigEntry, SwitchbotDataUpdateCoordinator
from .entity import SwitchbotConnectionPolledEntity, SwitchbotEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class SwitchBotSensorEntityDescription(SensorEntityDescription):
    """Describes SwitchBot sensor entities with optional value transformation."""

    value_fn: Callable[[str | int | None], str | int | None] = lambda v: v


SENSOR_TYPES: dict[str, SwitchBotSensorEntityDescription] = {
    "rssi": SwitchBotSensorEntityDescription(
        key="rssi",
        translation_key="bluetooth_signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "battery": SwitchBotSensorEntityDescription(
        key="battery",
        native_unit_of_measurement=UnitOfRatio.PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "co2": SwitchBotSensorEntityDescription(
        key="co2",
        native_unit_of_measurement=UnitOfRatio.PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.CO2,
    ),
    "humidity": SwitchBotSensorEntityDescription(
        key="humidity",
        native_unit_of_measurement=UnitOfRatio.PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.HUMIDITY,
    ),
    "temperature": SwitchBotSensorEntityDescription(
        key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwitchbotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Switchbot sensor based on a config entry."""
    coordinator = entry.runtime_data
    parsed_data = coordinator.device.parsed_data
    sensors: set[str] = {sensor for sensor in parsed_data if sensor in SENSOR_TYPES}
    sensor_entities: list[SensorEntity] = [
        SwitchBotSensor(coordinator, sensor) for sensor in sensors
    ]
    if isinstance(coordinator.device, switchbot.SwitchbotMeterPro):
        sensor_entities.append(SwitchBotMeterProFirmwareSensor(coordinator))
    sensor_entities.append(SwitchbotRSSISensor(coordinator, "rssi"))
    async_add_entities(sensor_entities)


class SwitchBotMeterProFirmwareSensor(
    SwitchbotConnectionPolledEntity, SensorEntity
):
    """Diagnostic sensor for Meter Pro firmware version."""

    _device: switchbot.SwitchbotMeterPro
    _attr_translation_key = "firmware"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize firmware sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}-firmware"

    @property
    @override
    def native_value(self) -> str | None:
        """Return firmware version."""
        if (fw := self.parsed_data.get("firmware")) is not None:
            return f"{fw:.1f}" if isinstance(fw, (int, float)) else str(fw)
        return None

    @override
    async def _async_read_value(self) -> None:
        """Fetch basic info from device to populate firmware version."""
        info = await self._device.get_basic_info()
        if info and "firmware" in info:
            self._device._override_state({"firmware": info["firmware"]})
            self._attr_native_value = f"{info['firmware']:.1f}"


class SwitchBotSensor(SwitchbotEntity, SensorEntity):
    """Representation of a Switchbot sensor."""

    entity_description: SwitchBotSensorEntityDescription

    def __init__(
        self,
        coordinator: SwitchbotDataUpdateCoordinator,
        sensor: str,
    ) -> None:
        """Initialize the Switchbot sensor."""
        super().__init__(coordinator)
        self._sensor = sensor
        self._channel = None
        self.entity_description = SENSOR_TYPES[sensor]
        self._attr_unique_id = f"{coordinator.base_unique_id}-{sensor}"

    @property
    @override
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.parsed_data.get(self._sensor))


class SwitchbotRSSISensor(SwitchBotSensor):
    """Representation of a Switchbot RSSI sensor."""

    @property
    @override
    def native_value(self) -> str | int | None:
        """Return the state of the sensor."""
        # Switchbot supports both connectable and non-connectable devices
        # so we need to request the rssi value based on the connectable instead
        # of the nearest scanner since that is the RSSI that matters for controlling
        # the device.
        if service_info := async_last_service_info(
            self.hass, self._address, self.coordinator.connectable
        ):
            return service_info.rssi
        return None
