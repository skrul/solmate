"""Sensor platform for solmate integration."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the sensor platform."""
    _LOGGER.info("Setting up sensor platform")
    _LOGGER.info(entry.options)
    async_add_entities(
        [
            SurplusPowerSensor(
                hass,
                entry.options["home_consumption_entity"],
                entry.options["pv_production_entity"],
                entry.options["power_buffer"],
            ),
        ]
    )


class SurplusPowerSensor(SensorEntity):
    """Sensor for calculating surplus power."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_has_entity_name = True
    _attr_name = "Surplus Power"
    _attr_unique_id = "solmate_surplus_power"

    def __init__(
        self,
        hass: HomeAssistant,
        home_consumption_entity: str,
        pv_production_entity: str,
        power_buffer: int,
    ) -> None:
        """Initialize the sensor."""
        self._hass = hass
        self._home_consumption_entity = home_consumption_entity
        self._pv_production_entity = pv_production_entity
        self._power_buffer = power_buffer

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""

        @callback
        def async_state_changed_listener(event: Event[EventStateChangedData]):
            """Handle state changes."""
            _LOGGER.info("state change!")
            _LOGGER.info(event.data)
            self.async_schedule_update_ha_state(True)

        self.async_on_remove(
            async_track_state_change_event(
                self._hass,
                [
                    self._home_consumption_entity,
                    self._pv_production_entity,
                ],
                async_state_changed_listener,
            )
        )

    @property
    def native_value(self):
        """Return the surplus power value."""
        try:
            # _LOGGER.info("native value!")
            consumption = float(
                self._hass.states.get(self._home_consumption_entity).state
            )
            production = float(self._hass.states.get(self._pv_production_entity).state)

            surplus = production - consumption - self._power_buffer
            # _LOGGER.info(consumption)
            # _LOGGER.info(production)
            # _LOGGER.info(surplus)
            return max(0, round(surplus))  # Don't return negative surplus

        except (ValueError, AttributeError) as err:
            _LOGGER.error("Error calculating surplus power: %s", err)
            return None
