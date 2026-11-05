"""An abstract class common to all Switchbot entities."""

from collections.abc import Callable, Coroutine, Mapping
import contextlib
import logging
from typing import Any, Concatenate, override

from bleak.exc import BleakError
import switchbot
from switchbot import Switchbot, SwitchbotDevice, SwitchbotOperationError

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothCoordinatorEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.start import async_at_started

from .const import DOMAIN, MANUFACTURER
from .coordinator import SwitchbotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class SwitchbotEntity(
    PassiveBluetoothCoordinatorEntity[SwitchbotDataUpdateCoordinator]
):
    """Generic entity encapsulating common features of Switchbot device."""

    _device: SwitchbotDevice
    _attr_has_entity_name = True

    def __init__(self, coordinator: SwitchbotDataUpdateCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device = coordinator.device
        self._last_run_success: bool | None = None
        self._address = coordinator.ble_device.address
        self._attr_unique_id = coordinator.base_unique_id
        connections = {(dr.CONNECTION_BLUETOOTH, self._address)}
        # MacOS Bluetooth addresses are not mac addresses. If the bluetooth
        # address is also a mac address, add this connection as well to prevent
        # a new device entry from being created when upgrading from a previous
        # version of the integration.
        if ":" in self._address:
            connections.add((dr.CONNECTION_NETWORK_MAC, self._address))
        sw_version = coordinator.device.parsed_data.get("firmware")
        if isinstance(sw_version, (int, float)):
            sw_version_str = f"{sw_version:.1f}"
        elif sw_version is not None:
            sw_version_str = str(sw_version)
        else:
            sw_version_str = None
        self._attr_device_info = DeviceInfo(
            connections=connections,
            manufacturer=MANUFACTURER,
            # Sometimes the modelName is missing from ads
            model=coordinator.model,
            name=coordinator.device_name,
            sw_version=sw_version_str,
        )
        self._channel: int | None = None

    @property
    def parsed_data(self) -> dict[str, Any]:
        """Return parsed device data for this entity."""
        return self.coordinator.device.parsed_data

    @property
    @override
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        return {"last_run_success": self._last_run_success}

    @callback
    def _async_update_attrs(self) -> None:
        """Update the entity attributes."""
        if (
            self._attr_device_info
            and self._attr_device_info.get("sw_version") is None
            and (fw := self.parsed_data.get("firmware")) is not None
        ):
            sw_str = f"{fw:.1f}" if isinstance(fw, (int, float)) else str(fw)
            self._attr_device_info = DeviceInfo(
                **{**self._attr_device_info, "sw_version": sw_str}
            )

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        """Handle data update."""
        self._async_update_attrs()
        self.async_write_ha_state()

    @override
    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(self._device.subscribe(self._handle_coordinator_update))
        return await super().async_added_to_hass()

    @override
    async def async_update(self) -> None:
        """Update the entity.

        Only used by the generic entity update service.
        """
        await self._device.update()


class SwitchbotConnectionPolledEntity(SwitchbotEntity):
    """Entity whose value has to be read from the device over a connection.

    Reading needs an active connection, which is slow and frequently
    impossible while Home Assistant is still starting up and competing for the
    Bluetooth adapter, so the first read is deferred until startup is over.
    """

    @property
    @override
    def should_poll(self) -> bool:
        """Poll, since the value is only readable over a connection."""
        return True

    async def _async_read_value(self) -> None:
        """Read the value from the device into the entity attributes."""
        raise NotImplementedError

    @override
    async def async_added_to_hass(self) -> None:
        """Register callbacks and read the value once startup is over."""
        await super().async_added_to_hass()
        self.async_on_remove(async_at_started(self.hass, self._async_hass_started))

    @callback
    def _async_hass_started(self, _hass: HomeAssistant) -> None:
        """Read the value now that startup is no longer in the way."""
        # A background task so a stuck connect is cancelled when the entry
        # unloads instead of holding up shutdown.
        self.coordinator.config_entry.async_create_background_task(
            self.hass,
            self.async_update_ha_state(force_refresh=True),
            f"switchbot_enhanced read {self.entity_id}",
        )

    @override
    async def async_update(self) -> None:
        """Read the value from the device."""
        ble_device = None
        if self.hass:
            with contextlib.suppress(Exception):
                ble_device = bluetooth.async_ble_device_from_address(
                    self.hass, self._address, connectable=True
                )
        if ble_device:
            self._device._device = ble_device
        else:
            _LOGGER.debug("No connectable path to %s, skipping update", self._address)
            return
        try:
            if self.coordinator.device.parsed_data.get("firmware") is None:
                with contextlib.suppress(Exception):
                    await self._device.get_basic_info()
            await self._async_read_value()
        except (SwitchbotOperationError, BleakError):
            _LOGGER.debug(
                "Failed to read %s from %s",
                self.entity_id,
                self._address,
                exc_info=True,
            )
            return


def exception_handler[_EntityT: SwitchbotEntity, **_P](
    func: Callable[Concatenate[_EntityT, _P], Coroutine[Any, Any, Any]],
) -> Callable[Concatenate[_EntityT, _P], Coroutine[Any, Any, None]]:
    """Decorate Switchbot calls to handle exceptions..

    A decorator that wraps the passed in function, catches Switchbot errors.
    """

    async def handler(self: _EntityT, *args: _P.args, **kwargs: _P.kwargs) -> None:
        try:
            await func(self, *args, **kwargs)
        except SwitchbotOperationError as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="operation_error",
                translation_placeholders={"error": str(error)},
            ) from error

    return handler


class SwitchbotSwitchedEntity(SwitchbotEntity, ToggleEntity):
    """Base class for Switchbot entities that can be turned on and off."""

    _device: Switchbot

    @exception_handler
    @override
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn device on."""
        _LOGGER.debug("Turn Switchbot device on %s", self._address)

        self._last_run_success = bool(await self._device.turn_on())
        if self._last_run_success:
            self._attr_is_on = True
        self.async_write_ha_state()

    @exception_handler
    @override
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn device off."""
        _LOGGER.debug("Turn Switchbot device off %s", self._address)

        self._last_run_success = bool(await self._device.turn_off())
        if self._last_run_success:
            self._attr_is_on = False
        self.async_write_ha_state()
