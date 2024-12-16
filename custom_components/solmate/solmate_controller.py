"""Solmate Controller."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .solmate_state_machine import SolmateStateMachine

_LOGGER = logging.getLogger(__name__)


class SolmateController:
    """Solmate Controller."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._hass = hass
        self._entry = entry
        self._sm = SolmateStateMachine()
        self._sm.add_listener(LogListener())
        self._sm.add_listener(EventProducingListener(hass, entry))
        self._state_change_callback_remover = None
        self._home_consumption_entity = entry.options["home_consumption_entity"]
        self._pv_production_entity = entry.options["pv_production_entity"]
        self._power_buffer = entry.options["power_buffer"]

    def _state_changed_listener(self, event: Event[EventStateChangedData]):
        """Handle state changes."""
        _LOGGER.info("State changed: %s", event)

    def start(self) -> None:
        """Start the state machine."""

        _LOGGER.info("Starting solmate controller")

        @callback
        def async_state_changed_listener(event: Event[EventStateChangedData]):
            """Handle state changes."""
            self._state_changed_listener(event)

        self._state_change_callback_remover = async_track_state_change_event(
            self._hass,
            [
                self._home_consumption_entity,
                self._pv_production_entity,
            ],
            async_state_changed_listener,
        )

        self._sm.send("ha_startup")

    def stop(self) -> None:
        """Stop the state machine."""
        if self._state_change_callback_remover:
            self._state_change_callback_remover()


class LogListener:
    """Log listener."""

    def after_transition(self, event, source, target):
        """Log after transition."""
        _LOGGER.info(
            "STATE MACHINE: after transition %s --%s--> %s",
            source.id,
            event,
            target.id,
        )

    def on_enter_state(self, target, event):
        """Log enter state."""
        _LOGGER.info(
            "STATE MACHINE: Entering %s from event %s",
            target.id,
            event,
        )


class EventProducingListener:
    """Log listener."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the listener."""
        self._hass = hass
        self._entry = entry

    def on_enter_state(self, target, event):
        """Log enter state."""
        _LOGGER.info(
            "STATE MACHINE !!!!: Entering %s from event %s: %s",
            target.id,
            event,
            self._entry.entry_id,
        )
        self._hass.bus.async_fire(
            "solmate_state_changed_event",
            {ATTR_ENTITY_ID: self._entry.entry_id, "event": event, "target": target.id},
        )
