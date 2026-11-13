"""Services for the SwitchBot Meter Pro integration."""

import contextlib
try:
    import probatio as vol
except ImportError:
    import voluptuous as vol

import switchbot

from homeassistant.components import bluetooth
from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, service

from .const import DOMAIN
from .coordinator import SwitchbotConfigEntry

SERVICE_SET_WEATHER = "meter_pro_set_weather"
SERVICE_SET_EXTERNAL_SENSOR_MAC = "meter_pro_set_external_sensor_mac"
SERVICE_SEND_RAW_COMMAND = "meter_pro_send_raw_command"

ATTR_ICON = "icon"
ATTR_TEMPERATURE = "temperature"
ATTR_HUMIDITY = "humidity"
ATTR_MAC_ADDRESS = "mac_address"
ATTR_SLOT = "slot"
ATTR_SWITCH_DISPLAY = "switch_display"
ATTR_COMMAND = "command"

ICON_MAP = {
    "none": 0,
    "sunny": 1,
    "partly_cloudy": 2,
    "cloudy": 3,
    "rainy": 4,
    "pouring": 5,
    "heavy_rain": 5,
    "snowy": 6,
    "light_snow": 6,
    "heavy_snow": 7,
}

SCHEMA_SET_WEATHER_SERVICE = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Optional(ATTR_ICON): vol.In(list(ICON_MAP.keys())),
        vol.Optional(ATTR_TEMPERATURE): vol.Coerce(float),
        vol.Optional(ATTR_HUMIDITY): vol.Coerce(float),
    },
    extra=vol.ALLOW_EXTRA,
)

SCHEMA_SET_EXTERNAL_SENSOR_MAC_SERVICE = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_MAC_ADDRESS): cv.string,
        vol.Optional(ATTR_SLOT, default=1): vol.All(
            vol.Coerce(int), vol.In([1, 2])
        ),
        vol.Optional(ATTR_SWITCH_DISPLAY, default=True): cv.boolean,
    },
    extra=vol.ALLOW_EXTRA,
)

SCHEMA_SEND_RAW_COMMAND_SERVICE = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_COMMAND): cv.string,
    },
    extra=vol.ALLOW_EXTRA,
)


@callback
def _async_get_switchbot_entry_for_device_id(
    hass: HomeAssistant, device_id: str
) -> SwitchbotConfigEntry:
    """Return the loaded SwitchBot config entry for a device id."""
    config_entry: SwitchbotConfigEntry
    _, config_entry = service.async_get_device_and_config_entry(hass, DOMAIN, device_id)
    return config_entry


async def async_meter_pro_set_weather(call: ServiceCall) -> None:
    """Push weather icon, temperature and humidity to Meter Pro."""
    device_id: str = call.data[ATTR_DEVICE_ID]
    icon_str: str | None = call.data.get(ATTR_ICON)

    entry = _async_get_switchbot_entry_for_device_id(call.hass, device_id)
    coordinator = entry.runtime_data
    if not isinstance(coordinator.device, switchbot.SwitchbotMeterPro):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="not_meter_pro_device",
        )

    if call.hass:
        with contextlib.suppress(Exception):
            if ble_device := bluetooth.async_ble_device_from_address(
                call.hass, coordinator.ble_device.address, connectable=True
            ):
                coordinator.device._device = ble_device

    await coordinator.device.set_weather(
        icon=ICON_MAP[icon_str] if icon_str is not None else None,
        temperature_c=call.data.get(ATTR_TEMPERATURE),
        humidity=call.data.get(ATTR_HUMIDITY),
    )


async def async_meter_pro_set_external_sensor_mac(call: ServiceCall) -> None:
    """Configure external sensor MAC address slot on Meter Pro."""
    device_id: str = call.data[ATTR_DEVICE_ID]
    mac_address: str = call.data[ATTR_MAC_ADDRESS]
    slot: int = call.data.get(ATTR_SLOT, 1)
    switch_display: bool = call.data.get(ATTR_SWITCH_DISPLAY, True)

    entry = _async_get_switchbot_entry_for_device_id(call.hass, device_id)
    coordinator = entry.runtime_data
    if not isinstance(coordinator.device, switchbot.SwitchbotMeterPro):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="not_meter_pro_device",
        )

    if call.hass:
        with contextlib.suppress(Exception):
            if ble_device := bluetooth.async_ble_device_from_address(
                call.hass, coordinator.ble_device.address, connectable=True
            ):
                coordinator.device._device = ble_device

    await coordinator.device.set_external_sensor_mac(
        mac_address=mac_address,
        slot=slot,
        switch_display=switch_display,
    )


async def async_meter_pro_send_raw_command(call: ServiceCall) -> ServiceResponse:
    """Send a raw hex command to a Meter Pro and return its raw response."""
    entry = _async_get_switchbot_entry_for_device_id(
        call.hass, call.data[ATTR_DEVICE_ID]
    )
    coordinator = entry.runtime_data
    if not isinstance(coordinator.device, switchbot.SwitchbotMeterPro):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="not_meter_pro_device",
        )
    result = await coordinator.device._send_command(call.data[ATTR_COMMAND])
    return {"response": result.hex() if result is not None else None}


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the services for the SwitchBot integration."""
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_WEATHER,
        async_meter_pro_set_weather,
        schema=SCHEMA_SET_WEATHER_SERVICE,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_EXTERNAL_SENSOR_MAC,
        async_meter_pro_set_external_sensor_mac,
        schema=SCHEMA_SET_EXTERNAL_SENSOR_MAC_SERVICE,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_RAW_COMMAND,
        async_meter_pro_send_raw_command,
        schema=SCHEMA_SEND_RAW_COMMAND_SERVICE,
        supports_response=SupportsResponse.ONLY,
    )
