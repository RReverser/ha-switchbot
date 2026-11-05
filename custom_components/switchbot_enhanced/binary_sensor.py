"""Support for SwitchBot Meter Pro CO2 binary sensors."""

from typing import override

import switchbot

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SwitchbotConfigEntry, SwitchbotDataUpdateCoordinator
from .entity import SwitchbotConnectionPolledEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwitchbotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SwitchBot Meter Pro CO2 binary sensors based on a config entry."""
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    if isinstance(coordinator.device, switchbot.SwitchbotMeterProCO2):
        entities.append(SwitchBotMeterProCO2PowerBinarySensor(coordinator))
    async_add_entities(entities)


class SwitchBotMeterProCO2PowerBinarySensor(
    SwitchbotConnectionPolledEntity, BinarySensorEntity
):
    """Diagnostic binary sensor for USB-C power connection status."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_translation_key = "usb_c_status"
    _attr_device_class = BinarySensorDeviceClass.PLUG
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize USB-C status binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}-usb_c_status"

    @property
    @override
    def is_on(self) -> bool | None:
        """Return True if connected to USB-C power."""
        if (plugged := self.parsed_data.get("power_type_c")) is not None:
            return plugged
        return self._attr_is_on

    @override
    async def _async_read_value(self) -> None:
        """Fetch USB-C power status from device."""
        status = await self._device.get_power_status()
        self._attr_is_on = status["plugged_in"]
        self._device._override_state({"power_type_c": status["plugged_in"]})
