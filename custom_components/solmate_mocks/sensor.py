"""Sensor platform for solmate_mocks integration."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import Event, EventStateChangedData, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "solmate_mocks_state"

DEFAULT_VALUES = {
    "home_power": 1500,
    "pv_production": 3000,
    "battery_soc": 75,
    "fast_charge": False,
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
            MockHomePowerSensor(hass, store),
            MockPVProductionSensor(hass, store),
            MockBatterySoCSensor(hass, store),
        ]
    )


class MockSensor(SensorEntity):
    """MockSensor."""

    def __init__(self, hass: HomeAssistant, store: Store, store_key: str) -> None:
        """Initialize the sensor."""
        self._hass = hass
        self._store = store
        self._store_key = store_key

    async def async_added_to_hass(self) -> None:
        """Load the stored state when added to hass."""

        async def async_state_changed_listener(event: Event[EventStateChangedData]):
            """Handle state changes."""
            new_state = event.data["new_state"].state
            self._attr_native_value = new_state
            stored_states = await self._store.async_load() or {}
            stored_states[self._store_key] = new_state
            await self._store.async_save(stored_states)
            self.async_write_ha_state()
            self.async_schedule_update_ha_state(True)

        self.async_on_remove(
            async_track_state_change_event(
                self._hass,
                ["sensor.mock_pv_production"],
                async_state_changed_listener,
            )
        )

        stored_states = await self._store.async_load()
        if stored_states and self._store_key in stored_states:
            self._attr_native_value = stored_states[self._store_key]


class MockHomePowerSensor(SensorEntity):
    """Sensor for mocking home power consumption."""

    _attr_name = "Mock Home Power Consumption"
    _attr_unique_id = "mock_home_power_consumption"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, store: Store) -> None:
        """Initialize the sensor."""
        super().__init__(hass, store, "pv_production")
        self._attr_native_value = DEFAULT_VALUES["home_power"]


class MockPVProductionSensor(MockSensor):
    """Sensor for mocking PV production."""

    _attr_name = "Mock PV Production"
    _attr_unique_id = "mock_pv_production"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, store: Store) -> None:
        """Initialize the sensor."""
        super().__init__(hass, store, "pv_production")
        self._attr_native_value = DEFAULT_VALUES["pv_production"]


class MockBatterySoCSensor(SensorEntity):
    """Sensor for mocking battery state of charge."""

    _attr_name = "Mock Battery SoC"
    _attr_unique_id = "mock_battery_soc"
    _attr_native_unit_of_measurement = "%"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass: HomeAssistant, store: Store) -> None:
        """Initialize the sensor."""
        super().__init__(hass, store, "battery_soc")
        self._attr_native_value = DEFAULT_VALUES["battery_soc"]
