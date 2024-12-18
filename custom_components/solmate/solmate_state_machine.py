"""Solmate State Machine."""

from datetime import datetime, timedelta
import logging

import statemachine as sm
from statemachine.contrib.diagram import DotGraphMachine

from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

CHARGE_START_DEBOUNCE = timedelta(seconds=3)


class SolmateStateMachine(sm.StateMachine):
    """Solmate State Machine."""

    # States
    initial = sm.State(initial=True)
    reset = sm.State()
    not_charging = sm.State()
    charge_start_pending = sm.State()
    charging_warmup = sm.State()
    charging = sm.State()
    stop_charge_pending = sm.State()
    charging_cooldown = sm.State()
    shutdown = sm.State(final=True)

    # Transitions
    ha_startup = initial.to(reset, cond="is_car_present") | initial.to(
        not_charging, cond="is_car_not_present"
    )

    reset_complete = reset.to(not_charging)

    start_charge_on_surplus = (
        not_charging.to(charge_start_pending)
        | charging.to.itself()
        | stop_charge_pending.to(charging)
    )

    stop_charge_on_surplus = charging.to(stop_charge_pending) | charge_start_pending.to(
        not_charging
    )

    charge_start_timer_fired = charge_start_pending.to(charging_warmup)

    charge_load_found = charging_warmup.to(charging)

    charging_warmup_timeout_timer_fired = charging_warmup.to(charging_cooldown)

    manual_stop = charging.to(charging_cooldown)

    charge_stop_timer_fired = stop_charge_pending.to(charging_cooldown)

    charge_load_lost = charging_cooldown.to(not_charging)

    shutdown_triggered = not_charging.to(shutdown)

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the state machine."""
        super().__init__(allow_event_without_transition=True)
        self._hass = hass
        self._charging_detected = False
        self._car_present = False

        self._unsub_charge_start_pending_timer = None
        self._unsub_charge_stop_pending_timer = None

    # Condition methods
    def is_car_present(self, state):
        """Check if car is present."""
        return self._car_present

    def is_car_not_present(self, state):
        """Check if car is not present."""
        return not self._car_present

    def is_charging_detected(self, state):
        """Check if charging is detected."""
        return self._charging_detected

    def is_charging_stopped(self, state):
        """Check if charging has stopped."""
        return not self._charging_detected

    # State entry methods
    def on_enter_reset(self, state):
        """Handle reset state entry."""
        _LOGGER.info("Entering reset state")
        # Stop charging and restore stored amp value

    def on_enter_not_charging(self, state):
        """Handle not charging state entry."""
        _LOGGER.info("Entering not charging state")
        if self._unsub_charge_start_pending_timer:
            self._unsub_charge_start_pending_timer()
            self._unsub_charge_start_pending_timer = None
        # Stop charging

    def on_enter_charge_start_pending(self, state, surplus=None, target_amps=None):
        """Handle charge start pending state entry."""
        _LOGGER.info("On_enter_charge_start_pending surplus: %s", surplus)

        async def _charge_start_pending_timer_callback(now: datetime):
            _LOGGER.info("Charge start pending timer fired")
            self.send("charge_start_timer_fired")
            self._unsub_charge_start_pending_timer = None

        self._unsub_charge_start_pending_timer = async_call_later(
            self._hass, CHARGE_START_DEBOUNCE, _charge_start_pending_timer_callback
        )

    def on_enter_charging_warmup(self, state):
        """Handle charging warmup state entry."""
        # Set a timer for 1 minute
        _LOGGER.info("Starting charging warmup")
        # Set amps and start charging

    def on_enter_stop_charge_pending(self, state):
        """Handle stop charge pending state entry."""
        pass

    def on_enter_charging_cooldown(self, state):
        """Handle charging cooldown state entry."""
        _LOGGER.info("Starting charging cooldown")
        # Stop charging

    def on_enter_shutdown(self, state):
        """Handle shutdown state entry."""
        _LOGGER.info("Shutting down")
        # Stop charging


if __name__ == "__main__":
    sm = SolmateStateMachine()
    graph = DotGraphMachine(sm)
    graph().write_png("solmate_state_machine.png")
