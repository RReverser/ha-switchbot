"""Constants for the switchbot_enhanced integration.

Meter Pro / Meter Pro CO2 only. Other SwitchBot device families are handled
by the core ``switchbot`` integration; the shared BLE library (``switchbot``
package) is intentionally left untouched.
"""

from enum import StrEnum

import switchbot
from switchbot import SwitchbotModel

DOMAIN = "switchbot_enhanced"
MANUFACTURER = "switchbot"

# Config Attributes

DEFAULT_NAME = "Switchbot"


class SupportedModels(StrEnum):
    """Switchbot models supported by this integration."""

    METER_PRO = "meter_pro"
    METER_PRO_CO2 = "meter_pro_co2"


CONNECTABLE_SUPPORTED_MODEL_TYPES = {
    SwitchbotModel.METER_PRO: SupportedModels.METER_PRO,
    SwitchbotModel.METER_PRO_CO2: SupportedModels.METER_PRO_CO2,
}

NON_CONNECTABLE_SUPPORTED_MODEL_TYPES: dict[SwitchbotModel, SupportedModels] = {}

SUPPORTED_MODEL_TYPES = (
    CONNECTABLE_SUPPORTED_MODEL_TYPES | NON_CONNECTABLE_SUPPORTED_MODEL_TYPES
)

# Meter Pro / CO2 are not encrypted devices.
ENCRYPTED_MODELS: set[SwitchbotModel] = set()

ENCRYPTED_SWITCHBOT_MODEL_TO_CLASS: dict[
    SwitchbotModel, switchbot.SwitchbotEncryptedDevice
] = {}

HASS_SENSOR_TYPE_TO_SWITCHBOT_MODEL = {
    str(v): k for k, v in SUPPORTED_MODEL_TYPES.items()
}

# Legacy migration input; new entries use the product-specific types.
DEPRECATED_SENSOR_TYPE_HYGROMETER_CO2 = "hygrometer_co2"

# Config Defaults
DEFAULT_RETRY_COUNT = 3

# Config Options
CONF_RETRY_COUNT = "retry_count"
CONF_KEY_ID = "key_id"
CONF_ENCRYPTION_KEY = "encryption_key"
