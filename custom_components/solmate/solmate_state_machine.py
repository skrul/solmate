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
CHARGE_STOP_DEBOUNCE = timedelta(seconds=3)
CHARGE_SESSION_PAUSE = timedelta(seconds=10)


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
    paused = sm.State()
    shutdown = sm.State(final=True)

    # Transitions
    ha_startup = initial.to(reset, cond="is_car_present") | initial.to(
        not_charging, cond="not is_car_present"
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

    current_charging_amps_changed = (
        charging_warmup.to(charging, cond="current_charging_amps >= 5")
        | charging.to(charging_cooldown, cond="current_charging_amps < 5")
        | charging_cooldown.to(paused, cond="current_charging_amps == 0")
    )

    charging_warmup_timeout_timer_fired = charging_warmup.to(charging_cooldown)

    manual_stop = charging.to(charging_cooldown)

    charge_stop_timer_fired = stop_charge_pending.to(charging_cooldown)

    already_stopped = charging_cooldown.to(paused)

    charge_session_pause_timer_fired = paused.to(not_charging)

    shutdown_triggered = not_charging.to(shutdown)

    current_charging_amps: int = 0

    def __init__(
        self,
        hass: HomeAssistant,
        charger_requested_charging_amps_entity: str,
        charger_switch_entity: str,
    ) -> None:
        """Initialize the state machine."""
        super().__init__(allow_event_without_transition=True)
        self._hass = hass
        self._charger_requested_charging_amps_entity = (
            charger_requested_charging_amps_entity
        )
        self._charger_switch_entity = charger_switch_entity

        self._car_present = False
        self._last_target_amps = 0

        self._charge_start_pending_timer = Timer(
            hass, self, "charge_start_timer_fired", CHARGE_START_DEBOUNCE
        )
        self._charge_stop_pending_timer = Timer(
            hass, self, "charge_stop_timer_fired", CHARGE_STOP_DEBOUNCE
        )
        self._charge_session_pause_timer = Timer(
            hass, self, "charge_session_pause_timer_fired", CHARGE_SESSION_PAUSE
        )

    def is_car_present(self, state):
        """Check if car is present."""
        return True

    @reset.enter
    def do_reset(self, state):
        """Handle reset state entry."""
        _LOGGER.info("Entering reset state")
        self._hass.states.async_set(self._charger_switch_entity, "off")
        self.send("reset_complete")

    @charge_start_pending.enter
    def schedule_start_pending_timer(self, state):
        """Handle charge start pending state entry."""
        self._charge_start_pending_timer.start()

    @charge_start_pending.exit
    def clear_start_pending_timer(self, state):
        """Clear the charge start pending timer."""
        self._charge_start_pending_timer.cancel()

    @charging_warmup.enter
    def start_charging_warmup(self, state):
        """Set the requested charging amps."""
        self._hass.states.async_set(self._charger_requested_charging_amps_entity, 5.0)
        self._hass.states.async_set(self._charger_switch_entity, "on")

    @charging.enter
    def charge_at_target_amps(self, state, target_amps=None):
        """Start charging."""
        _LOGGER.info("Starting charging")
        if target_amps != self._last_target_amps:
            self._hass.states.async_set(
                self._charger_requested_charging_amps_entity, target_amps
            )
            self._last_target_amps = target_amps

    @stop_charge_pending.enter
    def schedule_stop_pending_timer(self, state):
        """Set the stop pending timer."""
        self._charge_stop_pending_timer.start()

    @stop_charge_pending.exit
    def clear_stop_pending_timer(self, state):
        """Clear the stop pending timer."""
        self._charge_stop_pending_timer.cancel()

    @charging_cooldown.enter
    def stop_charging(self, state):
        """Stop charging."""
        _LOGGER.info("Stopping charging")
        self._hass.states.async_set(self._charger_switch_entity, "off")
        if self.current_charging_amps == 0:
            self.send("already_stopped")

    @paused.enter
    def schedule_pause_timer(self, state):
        """Schedule the pause timer."""
        self._charge_session_pause_timer.start()

    @paused.exit
    def clear_pause_timer(self, state):
        """Clear the pause timer."""
        self._charge_session_pause_timer.cancel()


class Timer:
    """Timer."""

    def __init__(
        self,
        hass: HomeAssistant,
        state_machine: sm.StateMachine,
        event_name: str,
        delay: timedelta,
    ) -> None:
        """Initialize the timer."""
        self._hass = hass
        self._state_machine = state_machine
        self._event_name = event_name
        self._delay = delay
        self._unsub_timer = None

    def start(self):
        """Start the timer."""
        if self._unsub_timer:
            raise ValueError("Timer already started")

        async def _timer_callback(now: datetime):
            self._state_machine.send(self._event_name)
            self._unsub_timer = None

        self._unsub_timer = async_call_later(self._hass, self._delay, _timer_callback)

    def cancel(self):
        """Cancel the timer."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

    def stop(self):
        """Stop the timer."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None


if __name__ == "__main__":
    sm = SolmateStateMachine(None, None)
    graph = DotGraphMachine(sm)
    graph().write_png("out.png")
