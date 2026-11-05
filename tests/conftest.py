"""Test fixtures for ha-switchbot."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from bleak.backends.device import BLEDevice
import switchbot
from switchbot import SwitchbotModel

from custom_components.switchbot_enhanced.coordinator import SwitchbotDataUpdateCoordinator


@pytest.fixture
def mock_meter_pro_device():
    """Create a mock SwitchbotMeterPro device."""
    dev = MagicMock(spec=switchbot.SwitchbotMeterPro)
    dev.show_battery_level = AsyncMock()
    dev.set_time_display_format = AsyncMock()
    dev.set_date_display_format = AsyncMock()
    dev.set_button_function = AsyncMock()
    dev.get_comfortlevel = AsyncMock(
        return_value=(20.0, 26.0, 40, 60)
    )
    dev.set_comfortlevel = AsyncMock()
    dev.get_temperature_humidity_offsets = AsyncMock(
        return_value={"temperature_offset": 0.0, "humidity_offset": 0}
    )
    dev.set_temperature_humidity_offsets = AsyncMock()
    dev.set_datetime = AsyncMock()
    dev.get_datetime = AsyncMock(return_value={"12h_mode": False})
    dev.set_weather = AsyncMock()
    dev.set_temperature_update_interval = AsyncMock()
    dev.get_temperature_update_interval = AsyncMock(return_value=300)
    dev.refresh_measurements = AsyncMock()
    dev.get_button_function = AsyncMock(
        return_value={"change_unit": False, "change_data_source": False}
    )
    dev.set_button_toggle_unit = AsyncMock()
    dev.set_button_toggle_data_source = AsyncMock()
    return dev


@pytest.fixture
def mock_meter_pro_co2_device(mock_meter_pro_device):
    """Create a mock SwitchbotMeterProCO2 device."""
    dev = MagicMock(spec=switchbot.SwitchbotMeterProCO2)
    dev.show_battery_level = mock_meter_pro_device.show_battery_level
    dev.set_time_display_format = mock_meter_pro_device.set_time_display_format
    dev.set_date_display_format = mock_meter_pro_device.set_date_display_format
    dev.set_button_function = mock_meter_pro_device.set_button_function
    dev.get_comfortlevel = mock_meter_pro_device.get_comfortlevel
    dev.set_comfortlevel = mock_meter_pro_device.set_comfortlevel
    dev.get_temperature_humidity_offsets = mock_meter_pro_device.get_temperature_humidity_offsets
    dev.set_temperature_humidity_offsets = mock_meter_pro_device.set_temperature_humidity_offsets
    dev.set_datetime = mock_meter_pro_device.set_datetime
    dev.get_datetime = mock_meter_pro_device.get_datetime
    dev.set_weather = mock_meter_pro_device.set_weather
    dev.set_temperature_update_interval = mock_meter_pro_device.set_temperature_update_interval
    dev.get_temperature_update_interval = mock_meter_pro_device.get_temperature_update_interval
    dev.refresh_measurements = mock_meter_pro_device.refresh_measurements
    dev.get_button_function = mock_meter_pro_device.get_button_function
    dev.set_button_toggle_unit = mock_meter_pro_device.set_button_toggle_unit
    dev.set_button_toggle_data_source = mock_meter_pro_device.set_button_toggle_data_source

    # CO2 specific
    dev.set_alert_sound = AsyncMock()
    dev.get_alert_sound = AsyncMock(
        return_value={"volume": 3, "sound_on": True, "flash_on": True}
    )
    dev.silence_alarm = AsyncMock()
    dev.set_co2_update_interval = AsyncMock()
    dev.force_new_co2_measurement = AsyncMock()
    dev.calibrate_co2_sensor = AsyncMock()
    dev.get_co2_thresholds = AsyncMock(return_value=(1000, 1400))
    dev.set_co2_thresholds = AsyncMock()
    dev.get_time_offset = AsyncMock(return_value=300)
    dev.set_time_offset = AsyncMock()
    return dev


@pytest.fixture
def mock_ble_device():
    """Create a mock BLEDevice."""
    return BLEDevice(
        address="AA:BB:CC:DD:EE:FF",
        name="MeterPro",
        details={},
    )


@pytest.fixture
def mock_meter_pro_coordinator(mock_meter_pro_device, mock_ble_device):
    """Create a mock SwitchbotDataUpdateCoordinator for Meter Pro."""
    coord = MagicMock(spec=SwitchbotDataUpdateCoordinator)
    coord.device = mock_meter_pro_device
    coord.ble_device = mock_ble_device
    coord.base_unique_id = "aa:bb:cc:dd:ee:ff"
    coord.device_name = "Meter Pro Test"
    coord.model = SwitchbotModel.METER_PRO
    coord.data = {
        "battery": 85,
        "temperature": 21.5,
        "humidity": 45,
        "time_mode_24h": True,
        "display_time_offset": 5,
    }
    coord.last_run_success = True
    coord.async_request_refresh = AsyncMock()
    coord.config_entry = MagicMock()
    return coord


@pytest.fixture
def mock_meter_pro_co2_coordinator(mock_meter_pro_co2_device, mock_ble_device):
    """Create a mock SwitchbotDataUpdateCoordinator for Meter Pro CO2."""
    coord = MagicMock(spec=SwitchbotDataUpdateCoordinator)
    coord.device = mock_meter_pro_co2_device
    coord.ble_device = mock_ble_device
    coord.base_unique_id = "aa:bb:cc:dd:ee:ff"
    coord.device_name = "Meter Pro CO2 Test"
    coord.model = SwitchbotModel.METER_PRO_CO2
    coord.data = {
        "battery": 90,
        "temperature": 22.0,
        "humidity": 50,
        "co2": 650,
        "time_mode_24h": True,
        "display_time_offset": 0,
    }
    coord.last_run_success = True
    coord.async_request_refresh = AsyncMock()
    coord.config_entry = MagicMock()
    return coord
