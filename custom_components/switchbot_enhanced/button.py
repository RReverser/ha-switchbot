"""Button support for SwitchBot Meter Pro devices."""

import contextlib
import logging
from typing import override

import switchbot

from homeassistant.components import bluetooth
from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import SwitchbotConfigEntry, SwitchbotDataUpdateCoordinator
from .entity import SwitchbotEntity, exception_handler

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwitchbotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Switchbot button platform."""
    coordinator = entry.runtime_data
    entities: list[ButtonEntity] = []

    if isinstance(coordinator.device, switchbot.SwitchbotMeterPro):
        entities.extend(
            [
                SwitchBotMeterProSyncDateTimeButton(coordinator),
                SwitchBotMeterProRefreshButton(coordinator),
            ]
        )
        if isinstance(coordinator.device, switchbot.SwitchbotMeterProCO2):
            entities.extend(
                [
                    SwitchBotMeterProCO2ForceMeasurementButton(coordinator),
                    SwitchBotMeterProCO2CalibrateButton(coordinator),
                    SwitchBotMeterProCO2SilenceAlarmButton(coordinator),
                ]
            )

    if entities:
        async_add_entities(entities)


class SwitchBotMeterProSyncDateTimeButton(SwitchbotEntity, ButtonEntity):
    """Button to sync date and time on Meter Pro and Meter Pro CO2."""

    _device: switchbot.SwitchbotMeterPro
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "sync_datetime"

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the sync time button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_sync_datetime"

    @exception_handler
    @override
    async def async_press(self) -> None:
        """Sync time with Home Assistant."""
        now = dt_util.now()

        # Get UTC offset components
        utc_offset = now.utcoffset()
        utc_offset_hours, utc_offset_minutes = 0, 0
        if utc_offset is not None:
            total_seconds = int(utc_offset.total_seconds())
            utc_offset_hours = total_seconds // 3600
            utc_offset_minutes = abs(total_seconds % 3600) // 60

        timestamp = int(now.timestamp())

        _LOGGER.debug(
            "Syncing time for %s: timestamp=%s,"
            " utc_offset_hours=%s, utc_offset_minutes=%s",
            self._address,
            timestamp,
            utc_offset_hours,
            utc_offset_minutes,
        )

        if self.hass:
            with contextlib.suppress(Exception):
                if ble_device := bluetooth.async_ble_device_from_address(
                    self.hass, self._address, connectable=True
                ):
                    self._device._device = ble_device

        await self._device.set_datetime(
            timestamp=timestamp,
            utc_offset_hours=utc_offset_hours,
            utc_offset_minutes=utc_offset_minutes,
        )


class SwitchBotMeterProRefreshButton(SwitchbotEntity, ButtonEntity):
    """Button to trigger an immediate environmental measurement refresh."""

    _device: switchbot.SwitchbotMeterPro
    _attr_translation_key = "refresh_measurements"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize refresh measurements button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_refresh_measurements"

    @exception_handler
    @override
    async def async_press(self) -> None:
        """Trigger environmental measurement refresh."""
        if self.hass:
            with contextlib.suppress(Exception):
                if ble_device := bluetooth.async_ble_device_from_address(
                    self.hass, self._address, connectable=True
                ):
                    self._device._device = ble_device
        await self._device.refresh_measurements()


class SwitchBotMeterProCO2ForceMeasurementButton(SwitchbotEntity, ButtonEntity):
    """Button to force immediate CO2 measurement."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_translation_key = "force_co2_measurement"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize force measurement button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_force_co2_measurement"

    @exception_handler
    @override
    async def async_press(self) -> None:
        """Force a new CO2 measurement and read back the updated value."""
        if self.hass:
            with contextlib.suppress(Exception):
                if ble_device := bluetooth.async_ble_device_from_address(
                    self.hass, self._address, connectable=True
                ):
                    self._device._device = ble_device
        ppm = await self._device.force_new_co2_measurement(readback=True)
        if ppm is not None:
            self._device._override_state({"co2": ppm})
            self.coordinator.async_update_listeners()


class SwitchBotMeterProCO2CalibrateButton(SwitchbotEntity, ButtonEntity):
    """Button to initiate CO2 sensor recalibration."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_translation_key = "calibrate_co2"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize calibrate button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_calibrate_co2"

    @exception_handler
    @override
    async def async_press(self) -> None:
        """Trigger CO2 recalibration."""
        if self.hass:
            with contextlib.suppress(Exception):
                if ble_device := bluetooth.async_ble_device_from_address(
                    self.hass, self._address, connectable=True
                ):
                    self._device._device = ble_device
        await self._device.calibrate_co2_sensor()


class SwitchBotMeterProCO2SilenceAlarmButton(SwitchbotEntity, ButtonEntity):
    """Button to silence active CO2 buzzer sound and screen flashing."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_translation_key = "silence_alarm"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize silence alarm button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}_silence_alarm"

    @exception_handler
    @override
    async def async_press(self) -> None:
        """Silence active alarm."""
        if self.hass:
            with contextlib.suppress(Exception):
                if ble_device := bluetooth.async_ble_device_from_address(
                    self.hass, self._address, connectable=True
                ):
                    self._device._device = ble_device
        await self._device.silence_alarm()
