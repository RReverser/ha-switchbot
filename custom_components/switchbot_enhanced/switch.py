"""Support for SwitchBot Meter Pro switches."""

import logging
from typing import Any, override

import switchbot

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
)
from homeassistant.const import EntityCategory, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .coordinator import SwitchbotConfigEntry, SwitchbotDataUpdateCoordinator
from .entity import (
    SwitchbotConnectionPolledEntity,
    SwitchbotEntity,
    exception_handler,
)


PARALLEL_UPDATES = 0
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwitchbotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Switchbot based on a config entry."""
    coordinator = entry.runtime_data

    if isinstance(coordinator.device, switchbot.SwitchbotMeterPro):
        meter_switches: list[SwitchEntity] = [
            SwitchBotMeterProBatteryIndicatorSwitch(coordinator),
            SwitchBotMeterProDisplayDataSourceSwitch(coordinator),
            SwitchBotMeterProButtonToggleUnitSwitch(coordinator),
            SwitchBotMeterProButtonToggleDataSourceSwitch(coordinator),
        ]
        if isinstance(coordinator.device, switchbot.SwitchbotMeterProCO2):
            meter_switches.append(SwitchBotMeterProCO2BuzzerSoundSwitch(coordinator))
        async_add_entities(meter_switches)


class SwitchBotMeterProBatteryIndicatorSwitch(
    SwitchbotEntity, SwitchEntity, RestoreEntity
):
    """Representation of a Switchbot Meter Pro battery indicator toggle switch."""

    _device: switchbot.SwitchbotMeterPro
    _attr_translation_key = "battery_indicator"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the battery indicator switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}-battery_indicator"
        self._attr_is_on = True

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == STATE_ON

    @exception_handler
    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Show battery indicator on screen."""
        await self._device.show_battery_level(True)
        self._attr_is_on = True
        self.async_write_ha_state()

    @exception_handler
    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Hide battery indicator on screen."""
        await self._device.show_battery_level(False)
        self._attr_is_on = False
        self.async_write_ha_state()


class SwitchBotMeterProCO2BuzzerSoundSwitch(
    SwitchbotConnectionPolledEntity, SwitchEntity, RestoreEntity
):
    """Representation of a Switchbot Meter Pro CO2 buzzer audible alarm switch."""

    _device: switchbot.SwitchbotMeterProCO2
    _attr_translation_key = "buzzer_sound"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the buzzer sound switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}-buzzer_sound"
        self._attr_is_on = True

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == STATE_ON

    @override
    async def _async_read_value(self) -> None:
        """Fetch alert sound status from device."""
        sound = await self._device.get_alert_sound()
        self._attr_is_on = sound["sound_on"]

    @exception_handler
    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable audible buzzer on alarm."""
        await self._device.set_alert_sound(sound_on=True, volume=3)
        self._attr_is_on = True
        self.async_write_ha_state()

    @exception_handler
    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable audible buzzer on alarm (flash only)."""
        await self._device.set_alert_sound(sound_on=False, volume=3)
        self._attr_is_on = False
        self.async_write_ha_state()


class SwitchBotMeterProDisplayDataSourceSwitch(
    SwitchbotConnectionPolledEntity, SwitchEntity, RestoreEntity
):
    """Representation of a Switchbot Meter Pro IN/OUT sensor toggle switch."""

    _device: switchbot.SwitchbotMeterPro
    _attr_translation_key = "display_data_source"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the display data source switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}-display_data_source"
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == STATE_ON

    @override
    async def _async_read_value(self) -> None:
        """Fetch current display data source (outdoor/indoor) from device."""
        self._attr_is_on = await self._device.get_display_data_source()

    @exception_handler
    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch display to outdoor sensor."""
        await self._device.set_display_data_source(outdoor=True)
        self._attr_is_on = True
        self.async_write_ha_state()

    @exception_handler
    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch display to indoor sensor."""
        await self._device.set_display_data_source(outdoor=False)
        self._attr_is_on = False
        self.async_write_ha_state()


class SwitchBotMeterProButtonToggleUnitSwitch(
    SwitchbotConnectionPolledEntity, SwitchEntity, RestoreEntity
):
    """Switch to enable/disable toggling temperature unit via top physical button."""

    _device: switchbot.SwitchbotMeterPro
    _attr_translation_key = "button_toggle_unit"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}-button_toggle_unit"
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == STATE_ON
            self._device._button_change_unit = self._attr_is_on

    @override
    async def _async_read_value(self) -> None:
        """Fetch button function behavior from device."""
        btn = await self._device.get_button_function()
        self._attr_is_on = btn["change_unit"]
        self._device._button_change_unit = self._attr_is_on

    @exception_handler
    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable toggling unit on top button."""
        await self._device.set_button_toggle_unit(True)
        self._attr_is_on = True
        self.async_write_ha_state()

    @exception_handler
    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable toggling unit on top button."""
        await self._device.set_button_toggle_unit(False)
        self._attr_is_on = False
        self.async_write_ha_state()


class SwitchBotMeterProButtonToggleDataSourceSwitch(
    SwitchbotConnectionPolledEntity, SwitchEntity, RestoreEntity
):
    """Switch to enable/disable toggling data source via top physical button."""

    _device: switchbot.SwitchbotMeterPro
    _attr_translation_key = "button_toggle_data_source"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.base_unique_id}-button_toggle_data_source"
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == STATE_ON
            self._device._button_change_data_source = self._attr_is_on

    @override
    async def _async_read_value(self) -> None:
        """Fetch button function behavior from device."""
        btn = await self._device.get_button_function()
        self._attr_is_on = btn["change_data_source"]
        self._device._button_change_data_source = self._attr_is_on

    @exception_handler
    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable toggling data source on top button."""
        await self._device.set_button_toggle_data_source(True)
        self._attr_is_on = True
        self.async_write_ha_state()

    @exception_handler
    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable toggling data source on top button."""
        await self._device.set_button_toggle_data_source(False)
        self._attr_is_on = False
        self.async_write_ha_state()
