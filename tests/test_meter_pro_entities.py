"""Unit tests for SwitchBot Meter Pro and Meter Pro CO2 custom entities."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from switchbot import SwitchbotModel

from homeassistant.exceptions import ServiceValidationError
from custom_components.switchbot_enhanced.binary_sensor import (
    SwitchBotMeterProCO2PowerBinarySensor,
    async_setup_entry as async_setup_binary_sensor,
)
from custom_components.switchbot_enhanced.button import (
    SwitchBotMeterProCO2CalibrateButton,
    SwitchBotMeterProCO2ForceMeasurementButton,
    SwitchBotMeterProCO2SilenceAlarmButton,
    SwitchBotMeterProRefreshButton,
    SwitchBotMeterProSyncDateTimeButton,
    async_setup_entry as async_setup_button,
)
from custom_components.switchbot_enhanced.number import (
    SwitchBotMeterProCO2DisplayTimeOffsetNumber,
    SwitchBotMeterProCO2ThresholdGoodNumber,
    SwitchBotMeterProCO2ThresholdModerateNumber,
    SwitchBotMeterProComfortColdNumber,
    SwitchBotMeterProComfortDryNumber,
    SwitchBotMeterProComfortHotNumber,
    SwitchBotMeterProComfortWetNumber,
    SwitchBotMeterProHumidityOffsetNumber,
    SwitchBotMeterProTemperatureOffsetNumber,
    async_setup_entry as async_setup_number,
)
from custom_components.switchbot_enhanced.select import (
    SwitchBotMeterProCO2BuzzerVolumeSelect,
    SwitchBotMeterProCO2TimeFormatSelect,
    SwitchBotMeterProCO2UpdateIntervalSelect,
    SwitchBotMeterProDateFormatSelect,
    SwitchBotMeterProTemperatureUpdateIntervalSelect,
    SwitchBotMeterProWeatherConditionSelect,
    async_setup_entry as async_setup_select,
)
from custom_components.switchbot_enhanced.sensor import (
    SwitchBotMeterProFirmwareSensor,
    async_setup_entry as async_setup_sensor,
)
from custom_components.switchbot_enhanced.services import (
    ICON_MAP,
    async_meter_pro_set_external_sensor_mac,
    async_meter_pro_set_weather,
)
from custom_components.switchbot_enhanced.switch import (
    SwitchBotMeterProBatteryIndicatorSwitch,
    SwitchBotMeterProButtonToggleDataSourceSwitch,
    SwitchBotMeterProButtonToggleUnitSwitch,
    SwitchBotMeterProCO2BuzzerSoundSwitch,
    SwitchBotMeterProDisplayDataSourceSwitch,
    async_setup_entry as async_setup_switch,
)


# =========================================================================
# Switch Platform Tests
# =========================================================================

async def test_battery_indicator_switch(mock_meter_pro_coordinator):
    """Test battery indicator toggle switch."""
    entity = SwitchBotMeterProBatteryIndicatorSwitch(mock_meter_pro_coordinator)
    assert entity.unique_id == "aa:bb:cc:dd:ee:ff-battery_indicator"
    assert entity.translation_key == "battery_indicator"

    with patch.object(entity, "async_write_ha_state"):
        await entity.async_turn_off()
        mock_meter_pro_coordinator.device.show_battery_level.assert_awaited_once_with(False)
        assert entity.is_on is False

        await entity.async_turn_on()
        mock_meter_pro_coordinator.device.show_battery_level.assert_awaited_with(True)
        assert entity.is_on is True


async def test_buzzer_sound_switch(mock_meter_pro_co2_coordinator):
    """Test buzzer audible alarm switch."""
    entity = SwitchBotMeterProCO2BuzzerSoundSwitch(mock_meter_pro_co2_coordinator)
    assert entity.unique_id == "aa:bb:cc:dd:ee:ff-buzzer_sound"
    assert entity.translation_key == "buzzer_sound"

    with patch.object(entity, "async_write_ha_state"):
        await entity.async_turn_off()
        mock_meter_pro_co2_coordinator.device.set_alert_sound.assert_awaited_once_with(
            sound_on=False, volume=3
        )
        assert entity.is_on is False

        await entity.async_turn_on()
        mock_meter_pro_co2_coordinator.device.set_alert_sound.assert_awaited_with(
            sound_on=True, volume=3
        )
        assert entity.is_on is True

    await entity._async_read_value()
    mock_meter_pro_co2_coordinator.device.get_alert_sound.assert_awaited_once()
    assert entity.is_on is True


async def test_display_data_source_switch(mock_meter_pro_coordinator):
    """Test in/out sensor toggle switch."""
    entity = SwitchBotMeterProDisplayDataSourceSwitch(mock_meter_pro_coordinator)
    assert entity.unique_id == "aa:bb:cc:dd:ee:ff-display_data_source"
    assert entity.translation_key == "display_data_source"
    assert entity.is_on is False

    mock_meter_pro_coordinator.device.get_display_data_source = AsyncMock(return_value=True)
    await entity._async_read_value()
    assert entity.is_on is True

    mock_meter_pro_coordinator.device.get_display_data_source.return_value = False
    await entity._async_read_value()
    assert entity.is_on is False

    with patch.object(entity, "async_write_ha_state"):
        await entity.async_turn_on()
        mock_meter_pro_coordinator.device.set_display_data_source.assert_awaited_once_with(
            outdoor=True
        )
        assert entity.is_on is True

        await entity.async_turn_off()
        mock_meter_pro_coordinator.device.set_display_data_source.assert_awaited_with(
            outdoor=False
        )
        assert entity.is_on is False


async def test_switch_setup_entry(mock_meter_pro_coordinator, mock_meter_pro_co2_coordinator):
    """Test async_setup_entry for switch platform."""
    added_entities = []
    callback = lambda entities: added_entities.extend(entities)

    # Meter Pro (non-CO2): should add battery indicator, display data source, and button switches
    entry = MagicMock(runtime_data=mock_meter_pro_coordinator)
    await async_setup_switch(None, entry, callback)
    assert any(isinstance(e, SwitchBotMeterProBatteryIndicatorSwitch) for e in added_entities)
    assert any(isinstance(e, SwitchBotMeterProDisplayDataSourceSwitch) for e in added_entities)
    assert any(isinstance(e, SwitchBotMeterProButtonToggleUnitSwitch) for e in added_entities)
    assert any(isinstance(e, SwitchBotMeterProButtonToggleDataSourceSwitch) for e in added_entities)
    assert not any(isinstance(e, SwitchBotMeterProCO2BuzzerSoundSwitch) for e in added_entities)

    # Meter Pro CO2: should add battery indicator, display data source, button switches, and buzzer sound
    added_entities.clear()
    entry = MagicMock(runtime_data=mock_meter_pro_co2_coordinator)
    await async_setup_switch(None, entry, callback)
    assert any(isinstance(e, SwitchBotMeterProBatteryIndicatorSwitch) for e in added_entities)
    assert any(isinstance(e, SwitchBotMeterProDisplayDataSourceSwitch) for e in added_entities)
    assert any(isinstance(e, SwitchBotMeterProButtonToggleUnitSwitch) for e in added_entities)
    assert any(isinstance(e, SwitchBotMeterProButtonToggleDataSourceSwitch) for e in added_entities)
    assert any(isinstance(e, SwitchBotMeterProCO2BuzzerSoundSwitch) for e in added_entities)


# =========================================================================
# Select Platform Tests
# =========================================================================

async def test_time_format_select(mock_meter_pro_co2_coordinator):
    """Test time format select entity."""
    entity = SwitchBotMeterProCO2TimeFormatSelect(mock_meter_pro_co2_coordinator)
    assert entity.options == ["12h", "24h"]

    await entity._async_read_value()
    assert entity.current_option == "24h"

    with patch.object(entity, "async_write_ha_state"):
        await entity.async_select_option("12h")
        mock_meter_pro_co2_coordinator.device.set_time_display_format.assert_awaited_once_with(True)
        assert entity.current_option == "12h"

        await entity.async_select_option("24h")
        mock_meter_pro_co2_coordinator.device.set_time_display_format.assert_awaited_with(False)
        assert entity.current_option == "24h"


async def test_date_format_select(mock_meter_pro_coordinator):
    """Test date format select entity."""
    entity = SwitchBotMeterProDateFormatSelect(mock_meter_pro_coordinator)
    assert entity.options == ["mm_dd", "dd_mm"]

    with patch.object(entity, "async_write_ha_state"):
        await entity.async_select_option("dd_mm")
        mock_meter_pro_coordinator.device.set_date_display_format.assert_awaited_once_with(False)
        assert entity.current_option == "dd_mm"

        await entity.async_select_option("mm_dd")
        mock_meter_pro_coordinator.device.set_date_display_format.assert_awaited_with(True)
        assert entity.current_option == "mm_dd"


async def test_button_toggle_switches(mock_meter_pro_coordinator):
    """Test button toggle switches."""
    unit_switch = SwitchBotMeterProButtonToggleUnitSwitch(mock_meter_pro_coordinator)
    source_switch = SwitchBotMeterProButtonToggleDataSourceSwitch(mock_meter_pro_coordinator)

    await unit_switch._async_read_value()
    mock_meter_pro_coordinator.device.get_button_function.assert_awaited_once()

    await source_switch._async_read_value()

    with patch.object(unit_switch, "async_write_ha_state"):
        await unit_switch.async_turn_on()
        mock_meter_pro_coordinator.device.set_button_toggle_unit.assert_awaited_once_with(True)
        assert unit_switch.is_on is True

        await unit_switch.async_turn_off()
        mock_meter_pro_coordinator.device.set_button_toggle_unit.assert_awaited_with(False)
        assert unit_switch.is_on is False

    with patch.object(source_switch, "async_write_ha_state"):
        await source_switch.async_turn_on()
        mock_meter_pro_coordinator.device.set_button_toggle_data_source.assert_awaited_once_with(True)
        assert source_switch.is_on is True

        await source_switch.async_turn_off()
        mock_meter_pro_coordinator.device.set_button_toggle_data_source.assert_awaited_with(False)
        assert source_switch.is_on is False


async def test_buzzer_volume_select(mock_meter_pro_co2_coordinator):
    """Test buzzer volume select entity."""
    entity = SwitchBotMeterProCO2BuzzerVolumeSelect(mock_meter_pro_co2_coordinator)
    assert entity.options == ["low", "medium", "high"]

    with patch.object(entity, "async_write_ha_state"):
        await entity.async_select_option("high")
        mock_meter_pro_co2_coordinator.device.set_alert_sound.assert_awaited_once_with(
            sound_on=True, volume=4
        )
        assert entity.current_option == "high"


async def test_co2_update_interval_select(mock_meter_pro_co2_coordinator):
    """Test CO2 update interval select entity."""
    entity = SwitchBotMeterProCO2UpdateIntervalSelect(mock_meter_pro_co2_coordinator)
    assert entity.options == ["5m", "10m", "30m"]

    with patch.object(entity, "async_write_ha_state"):
        await entity.async_select_option("5m")
        mock_meter_pro_co2_coordinator.device.set_co2_update_interval.assert_awaited_once_with(300)
        assert entity.current_option == "5m"


async def test_temperature_update_interval_select(mock_meter_pro_coordinator):
    """Test temperature update interval select entity."""
    entity = SwitchBotMeterProTemperatureUpdateIntervalSelect(mock_meter_pro_coordinator)
    assert entity.options == ["5m", "10m", "30m"]

    with patch.object(entity, "async_write_ha_state"):
        await entity.async_select_option("10m")
        mock_meter_pro_coordinator.device.set_temperature_update_interval.assert_awaited_once_with(600)
        assert entity.current_option == "10m"


async def test_weather_condition_select(mock_meter_pro_coordinator):
    """Test weather condition select entity."""
    entity = SwitchBotMeterProWeatherConditionSelect(mock_meter_pro_coordinator)
    assert "sunny" in entity.options
    assert "heavy_snow" in entity.options
    assert "pouring" in entity.options
    assert entity.entity_registry_enabled_default is False

    from switchbot import MeterProWeatherIcon
    mock_meter_pro_coordinator.device.get_weather = AsyncMock(
        return_value={"icon": MeterProWeatherIcon.SUNNY}
    )
    await entity._async_read_value()
    assert entity.current_option == "sunny"

    with patch.object(entity, "async_write_ha_state"):
        await entity.async_select_option("pouring")
        mock_meter_pro_coordinator.device.set_weather.assert_awaited_once_with(
            icon=MeterProWeatherIcon.POURING
        )
        assert entity.current_option == "pouring"


async def test_select_setup_entry(mock_meter_pro_coordinator, mock_meter_pro_co2_coordinator):
    """Test async_setup_entry for select platform."""
    added_entities = []
    callback = lambda entities: added_entities.extend(entities)

    entry = MagicMock(runtime_data=mock_meter_pro_co2_coordinator)
    await async_setup_select(None, entry, callback)
    types = [type(e) for e in added_entities]
    assert SwitchBotMeterProCO2TimeFormatSelect in types
    assert SwitchBotMeterProDateFormatSelect in types
    assert SwitchBotMeterProTemperatureUpdateIntervalSelect in types
    assert SwitchBotMeterProWeatherConditionSelect in types
    assert SwitchBotMeterProCO2BuzzerVolumeSelect in types
    assert SwitchBotMeterProCO2UpdateIntervalSelect in types


# =========================================================================
# Number Platform Tests
# =========================================================================

async def test_comfort_range_numbers(mock_meter_pro_coordinator):
    """Test comfort temperature and humidity threshold numbers."""
    cold = SwitchBotMeterProComfortColdNumber(mock_meter_pro_coordinator)
    hot = SwitchBotMeterProComfortHotNumber(mock_meter_pro_coordinator)
    dry = SwitchBotMeterProComfortDryNumber(mock_meter_pro_coordinator)
    wet = SwitchBotMeterProComfortWetNumber(mock_meter_pro_coordinator)

    # Read value
    await cold._async_read_value()
    assert cold.native_value == 18.0
    await hot._async_read_value()
    assert hot.native_value == 26.0
    await dry._async_read_value()
    assert dry.native_value == 30
    await wet._async_read_value()
    assert wet.native_value == 70

    # Write value
    with patch.object(cold, "async_write_ha_state"):
        await cold.async_set_native_value(19.5)
        mock_meter_pro_coordinator.device.set_comfortlevel.assert_awaited_once_with(
            cold=19.5,
            hot=26.0,
            dry=30,
            wet=70,
        )


async def test_calibration_offset_numbers(mock_meter_pro_coordinator):
    """Test temperature and humidity calibration offset numbers."""
    t_offset = SwitchBotMeterProTemperatureOffsetNumber(mock_meter_pro_coordinator)
    h_offset = SwitchBotMeterProHumidityOffsetNumber(mock_meter_pro_coordinator)

    await t_offset._async_read_value()
    assert t_offset.native_value == 0.0
    await h_offset._async_read_value()
    assert h_offset.native_value == 0

    with patch.object(t_offset, "async_write_ha_state"):
        await t_offset.async_set_native_value(1.2)
        mock_meter_pro_coordinator.device.set_temperature_humidity_offsets.assert_awaited_once_with(
            temperature_offset=1.2,
            humidity_offset=0,
        )


async def test_co2_threshold_numbers(mock_meter_pro_co2_coordinator):
    """Test CO2 air quality target range numbers."""
    good = SwitchBotMeterProCO2ThresholdGoodNumber(mock_meter_pro_co2_coordinator)
    moderate = SwitchBotMeterProCO2ThresholdModerateNumber(mock_meter_pro_co2_coordinator)

    await good._async_read_value()
    assert good.native_value == 1000
    await moderate._async_read_value()
    assert moderate.native_value == 1400

    with patch.object(good, "async_write_ha_state"):
        await good.async_set_native_value(800)
        mock_meter_pro_co2_coordinator.device.set_co2_thresholds.assert_awaited_once_with(
            lower=800,
            upper=1400,
        )


async def test_display_time_offset_number(mock_meter_pro_co2_coordinator):
    """Test display time offset number."""
    offset_num = SwitchBotMeterProCO2DisplayTimeOffsetNumber(mock_meter_pro_co2_coordinator)
    await offset_num._async_read_value()
    assert offset_num.native_value == 5  # 300 seconds / 60 = 5 minutes

    with patch.object(offset_num, "async_write_ha_state"):
        await offset_num.async_set_native_value(10)
        mock_meter_pro_co2_coordinator.device.set_time_offset.assert_awaited_once_with(600)
        assert offset_num.native_value == 10


async def test_number_setup_entry(mock_meter_pro_coordinator, mock_meter_pro_co2_coordinator):
    """Test async_setup_entry for number platform."""
    added_entities = []
    callback = lambda entities: added_entities.extend(entities)

    entry = MagicMock(runtime_data=mock_meter_pro_co2_coordinator)
    await async_setup_number(None, entry, callback)
    types = [type(e) for e in added_entities]
    assert SwitchBotMeterProComfortColdNumber in types
    assert SwitchBotMeterProComfortHotNumber in types
    assert SwitchBotMeterProComfortDryNumber in types
    assert SwitchBotMeterProComfortWetNumber in types
    assert SwitchBotMeterProTemperatureOffsetNumber in types
    assert SwitchBotMeterProHumidityOffsetNumber in types
    assert SwitchBotMeterProCO2ThresholdGoodNumber in types
    assert SwitchBotMeterProCO2ThresholdModerateNumber in types
    assert SwitchBotMeterProCO2DisplayTimeOffsetNumber in types


# =========================================================================
# Button Platform Tests
# =========================================================================

async def test_meter_pro_buttons(mock_meter_pro_co2_coordinator):
    """Test Meter Pro button entities."""
    sync_btn = SwitchBotMeterProSyncDateTimeButton(mock_meter_pro_co2_coordinator)
    refresh_btn = SwitchBotMeterProRefreshButton(mock_meter_pro_co2_coordinator)
    force_btn = SwitchBotMeterProCO2ForceMeasurementButton(mock_meter_pro_co2_coordinator)
    calib_btn = SwitchBotMeterProCO2CalibrateButton(mock_meter_pro_co2_coordinator)
    silence_btn = SwitchBotMeterProCO2SilenceAlarmButton(mock_meter_pro_co2_coordinator)

    await sync_btn.async_press()
    mock_meter_pro_co2_coordinator.device.set_datetime.assert_awaited_once()

    await refresh_btn.async_press()
    mock_meter_pro_co2_coordinator.device.refresh_measurements.assert_awaited_once()

    mock_meter_pro_co2_coordinator.device.force_new_co2_measurement.return_value = 550
    await force_btn.async_press()
    mock_meter_pro_co2_coordinator.device.force_new_co2_measurement.assert_awaited_once_with(readback=True)

    await calib_btn.async_press()
    mock_meter_pro_co2_coordinator.device.calibrate_co2_sensor.assert_awaited_once()

    await silence_btn.async_press()
    mock_meter_pro_co2_coordinator.device.silence_alarm.assert_awaited_once()


async def test_button_setup_entry(mock_meter_pro_coordinator, mock_meter_pro_co2_coordinator):
    """Test async_setup_entry for button platform."""
    added_entities = []
    callback = lambda entities: added_entities.extend(entities)

    # Meter Pro: sync clock + refresh
    entry = MagicMock(runtime_data=mock_meter_pro_coordinator)
    await async_setup_button(None, entry, callback)
    assert any(isinstance(e, SwitchBotMeterProSyncDateTimeButton) for e in added_entities)
    assert any(isinstance(e, SwitchBotMeterProRefreshButton) for e in added_entities)
    assert not any(isinstance(e, SwitchBotMeterProCO2ForceMeasurementButton) for e in added_entities)

    # Meter Pro CO2: sync clock + refresh + force CO2 + calibrate CO2 + silence alarm
    added_entities.clear()
    entry = MagicMock(runtime_data=mock_meter_pro_co2_coordinator)
    await async_setup_button(None, entry, callback)
    assert any(isinstance(e, SwitchBotMeterProSyncDateTimeButton) for e in added_entities)
    assert any(isinstance(e, SwitchBotMeterProRefreshButton) for e in added_entities)
    assert any(isinstance(e, SwitchBotMeterProCO2ForceMeasurementButton) for e in added_entities)
    assert any(isinstance(e, SwitchBotMeterProCO2CalibrateButton) for e in added_entities)
    assert any(isinstance(e, SwitchBotMeterProCO2SilenceAlarmButton) for e in added_entities)


# =========================================================================
# Services Tests
# =========================================================================

async def test_meter_pro_set_weather_service(mock_meter_pro_coordinator):
    """Test meter_pro_set_weather service call."""
    call = MagicMock()
    call.data = {
        "device_id": "test_device_id",
        "icon": "sunny",
    }
    call.hass = MagicMock()

    mock_entry = MagicMock(runtime_data=mock_meter_pro_coordinator)
    with patch(
        "custom_components.switchbot_enhanced.services._async_get_switchbot_entry_for_device_id",
        return_value=mock_entry,
    ):
        await async_meter_pro_set_weather(call)
        mock_meter_pro_coordinator.device.set_weather.assert_awaited_once_with(
            icon=1,
        )


async def test_meter_pro_set_weather_service_invalid_device():
    """Test meter_pro_set_weather rejects devices that are not Meter Pro."""
    call = MagicMock()
    call.data = {
        "device_id": "test_device_id",
        "icon": "rainy",
    }
    call.hass = MagicMock()

    non_meter_pro = MagicMock()  # Not a SwitchbotMeterPro
    mock_coord = MagicMock(device=non_meter_pro)
    mock_entry = MagicMock(runtime_data=mock_coord)

    with patch(
        "custom_components.switchbot_enhanced.services._async_get_switchbot_entry_for_device_id",
        return_value=mock_entry,
    ):
        with pytest.raises(ServiceValidationError):
            await async_meter_pro_set_weather(call)


async def test_meter_pro_weather_icon_mappings():
    """Verify all weather icon mappings, especially the snow/rain fixes."""
    assert ICON_MAP["heavy_snow"] == 7
    assert ICON_MAP["light_snow"] == 6
    assert ICON_MAP["snowy"] == 6
    assert ICON_MAP["pouring"] == 5
    assert ICON_MAP["heavy_rain"] == 5
    assert ICON_MAP["rainy"] == 4
    assert ICON_MAP["cloudy"] == 3
    assert ICON_MAP["partly_cloudy"] == 2
    assert ICON_MAP["sunny"] == 1
    assert ICON_MAP["none"] == 0


async def test_meter_pro_set_external_sensor_mac_service(mock_meter_pro_coordinator):
    """Test meter_pro_set_external_sensor_mac service call."""
    call = MagicMock()
    call.data = {
        "device_id": "test_device_id",
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "slot": 1,
    }
    call.hass = MagicMock()

    mock_entry = MagicMock(runtime_data=mock_meter_pro_coordinator)
    with patch(
        "custom_components.switchbot_enhanced.services._async_get_switchbot_entry_for_device_id",
        return_value=mock_entry,
    ):
        await async_meter_pro_set_external_sensor_mac(call)
        mock_meter_pro_coordinator.device.set_external_sensor_mac.assert_awaited_once_with(
            mac_address="AA:BB:CC:DD:EE:FF",
            slot=1,
            switch_display=True,
        )

        # Test with explicit switch_display=False
        mock_meter_pro_coordinator.device.set_external_sensor_mac.reset_mock()
        call.data["switch_display"] = False
        await async_meter_pro_set_external_sensor_mac(call)
        mock_meter_pro_coordinator.device.set_external_sensor_mac.assert_awaited_once_with(
            mac_address="AA:BB:CC:DD:EE:FF",
            slot=1,
            switch_display=False,
        )


async def test_entity_registry_enabled_default_rules(mock_meter_pro_co2_coordinator):
    """Verify entity_registry_enabled_default rules.

    Only quality thresholds, time offset, and weather condition select should be disabled by default.
    All other entities should be enabled by default.
    """
    coord = mock_meter_pro_co2_coordinator

    # Disabled by default
    assert SwitchBotMeterProCO2ThresholdGoodNumber(coord).entity_registry_enabled_default is False
    assert SwitchBotMeterProCO2ThresholdModerateNumber(coord).entity_registry_enabled_default is False
    assert SwitchBotMeterProCO2DisplayTimeOffsetNumber(coord).entity_registry_enabled_default is False
    assert SwitchBotMeterProWeatherConditionSelect(coord).entity_registry_enabled_default is False

    # Enabled by default
    assert SwitchBotMeterProComfortColdNumber(coord).entity_registry_enabled_default is True
    assert SwitchBotMeterProComfortHotNumber(coord).entity_registry_enabled_default is True
    assert SwitchBotMeterProComfortDryNumber(coord).entity_registry_enabled_default is True
    assert SwitchBotMeterProComfortWetNumber(coord).entity_registry_enabled_default is True
    assert SwitchBotMeterProTemperatureOffsetNumber(coord).entity_registry_enabled_default is True
    assert SwitchBotMeterProHumidityOffsetNumber(coord).entity_registry_enabled_default is True
    assert SwitchBotMeterProCO2TimeFormatSelect(coord).entity_registry_enabled_default is True
    assert SwitchBotMeterProDateFormatSelect(coord).entity_registry_enabled_default is True
    assert SwitchBotMeterProButtonToggleUnitSwitch(coord).entity_registry_enabled_default is True
    assert SwitchBotMeterProButtonToggleDataSourceSwitch(coord).entity_registry_enabled_default is True
    assert SwitchBotMeterProCO2BuzzerVolumeSelect(coord).entity_registry_enabled_default is True
    assert SwitchBotMeterProCO2UpdateIntervalSelect(coord).entity_registry_enabled_default is True
    assert SwitchBotMeterProTemperatureUpdateIntervalSelect(coord).entity_registry_enabled_default is True


async def test_firmware_version_in_device_info(mock_meter_pro_coordinator):
    """Test that firmware version is read from parsed_data and set on device_info."""
    mock_meter_pro_coordinator.device.parsed_data = {"firmware": 2.1}
    entity = SwitchBotMeterProBatteryIndicatorSwitch(mock_meter_pro_coordinator)
    assert entity.device_info["sw_version"] == "2.1"

    # Test dynamic update when firmware is populated later
    mock_meter_pro_coordinator.device.parsed_data = {}
    entity_dynamic = SwitchBotMeterProBatteryIndicatorSwitch(mock_meter_pro_coordinator)
    assert entity_dynamic.device_info.get("sw_version") is None

    mock_meter_pro_coordinator.device.parsed_data = {"firmware": 1.5}
    entity_dynamic._async_update_attrs()
    assert entity_dynamic.device_info["sw_version"] == "1.5"


async def test_firmware_diagnostic_sensor(mock_meter_pro_coordinator):
    """Test firmware diagnostic sensor."""
    mock_meter_pro_coordinator.device.parsed_data = {"firmware": 1.5}
    mock_meter_pro_coordinator.device.get_basic_info = AsyncMock(
        return_value={"firmware": 1.5, "battery": 90}
    )
    sensor = SwitchBotMeterProFirmwareSensor(mock_meter_pro_coordinator)
    assert sensor.unique_id == "aa:bb:cc:dd:ee:ff-firmware"
    assert sensor.native_value == "1.5"
    await sensor._async_read_value()
    mock_meter_pro_coordinator.device.get_basic_info.assert_awaited_once()


async def test_usb_c_status_binary_sensor(mock_meter_pro_co2_coordinator):
    """Test USB-C status diagnostic binary sensor."""
    mock_meter_pro_co2_coordinator.device.parsed_data = {"power_type_c": True}
    mock_meter_pro_co2_coordinator.device.get_power_status = AsyncMock(
        return_value={"plugged_in": True}
    )
    sensor = SwitchBotMeterProCO2PowerBinarySensor(mock_meter_pro_co2_coordinator)
    assert sensor.unique_id == "aa:bb:cc:dd:ee:ff-usb_c_status"
    assert sensor.is_on is True

    mock_meter_pro_co2_coordinator.device.get_power_status = AsyncMock(
        return_value={"plugged_in": False}
    )
    await sensor._async_read_value()
    assert sensor.is_on is False
