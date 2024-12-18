"""Sensor platform for solmate_mocks integration."""

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "solmate_mocks_state"

DEFAULT_VALUES = {
    "home_power": 1500,
    "pv_production": 3000,
    "battery_soc": 75,
    "fast_charge": False,
    "current_charging_amps": 0,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the sensor platform."""
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    _LOGGER.info("Created store")
    _LOGGER.info(store)

    async_add_entities(
        [
            MockHomePowerSensor(hass, entry, store),
            MockPVProductionSensor(hass, entry, store),
            MockBatterySoCSensor(hass, entry, store),
            MockCurrentChargingAmpsSensor(hass, entry, store),
        ]
    )


class MockSensor(NumberEntity):
    """MockSensor."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, store: Store, store_key: str
    ) -> None:
        """Initialize the sensor."""
        self._hass = hass
        self._store = store
        self._store_key = store_key
        self._attr_device_info = DeviceInfo(
            name="Solmate Mocks",
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_set_native_value(self, value):
        """Update."""
        self._attr_native_value = value
        stored_states = await self._store.async_load() or {}
        stored_states[self._store_key] = value
        await self._store.async_save(stored_states)

    async def async_added_to_hass(self) -> None:
        """Load the stored state when added to hass."""

        stored_states = await self._store.async_load()
        if stored_states and self._store_key in stored_states:
            self._attr_native_value = stored_states[self._store_key]


class MockHomePowerSensor(MockSensor):
    """Sensor for mocking home power consumption."""

    _attr_name = "Mock Home Power Consumption"
    _attr_unique_id = "mock_home_power_consumption"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_mode = "auto"
    _attr_native_min_value = 0
    _attr_native_max_value = 100000

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: Store) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, store, "home_power")
        self._attr_native_value = DEFAULT_VALUES["home_power"]


class MockPVProductionSensor(MockSensor):
    """Sensor for mocking PV production."""

    _attr_name = "Mock PV Production"
    _attr_unique_id = "mock_pv_production"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_min_value = 0
    _attr_native_max_value = 100000

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: Store) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, store, "pv_production")
        self._attr_native_value = DEFAULT_VALUES["pv_production"]


class MockBatterySoCSensor(MockSensor):
    """Sensor for mocking battery state of charge."""

    _attr_name = "Mock Battery SoC"
    _attr_unique_id = "mock_battery_soc"
    _attr_native_unit_of_measurement = "%"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_min_value = 0
    _attr_native_max_value = 100

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: Store) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, store, "battery_soc")
        self._attr_native_value = DEFAULT_VALUES["battery_soc"]


class MockCurrentChargingAmpsSensor(MockSensor):
    """Sensor for mocking current charging amps."""

    _attr_name = "Mock Current Charging Amps"
    _attr_unique_id = "mock_current_charging_amps"
    _attr_native_unit_of_measurement = "A"
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_min_value = 0
    _attr_native_max_value = 48

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: Store) -> None:
        """Initialize the sensor."""
        super().__init__(hass, entry, store, "current_charging_amps")
        self._attr_native_value = DEFAULT_VALUES["current_charging_amps"]
