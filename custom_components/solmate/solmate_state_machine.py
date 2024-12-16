"""Solmate State Machine."""

from datetime import datetime, timedelta
import logging

import statemachine as sm
from statemachine.contrib.diagram import DotGraphMachine

_LOGGER = logging.getLogger(__name__)


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

    reset_complete = reset.to(not_charging)  # , on="stop_charging_command_success")

    surplus_updated = (
        not_charging.to(charge_start_pending, cond="has_sufficient_surplus")
        | charging.to(stop_charge_pending, cond="insufficient_surplus")
        | charge_start_pending.to(not_charging, cond="insufficient_surplus")
        | charging.to.itself(cond="has_sufficient_surplus")
        | stop_charge_pending.to(charging, cond="has_sufficient_surplus")
    )

    charge_start_timer_fired = charge_start_pending.to(charging_warmup)

    charge_load_found = charging_warmup.to(charging)

    charging_warmup_timeout_timer_fired = charging_warmup.to(charging_cooldown)

    manual_stop = charging.to(charging_cooldown)

    charge_stop_timer_fired = stop_charge_pending.to(charging_cooldown)

    charge_load_lost = charging_cooldown.to(not_charging)

    shutdown_triggered = not_charging.to(shutdown)

    def __init__(self) -> None:
        """Initialize the state machine."""
        super().__init__()
        self.surplus_power = 0
        self.buffer = 0
        self.charging_detected = False
        self.car_present = False
        self.pending_start_time = None
        self.pending_stop_time = None

    # Condition methods
    def is_car_present(self, state):
        """Check if car is present."""
        return self.car_present

    def is_car_not_present(self, state):
        """Check if car is not present."""
        return not self.car_present

    def has_sufficient_surplus(self, state):
        """Check if there's sufficient surplus power."""
        return self.surplus_power > self.buffer

    def insufficient_surplus(self, state):
        """Check if there's insufficient surplus power."""
        return self.surplus_power <= self.buffer

    def has_been_pending_one_minute(self, state):
        """Check if state has been pending for 1 minute."""
        if state.name == "charge_start_pending":
            pending_time = self.pending_start_time
        else:
            pending_time = self.pending_stop_time

        if pending_time is None:
            return False
        return datetime.now() - pending_time >= timedelta(minutes=1)

    def is_charging_detected(self, state):
        """Check if charging is detected."""
        return self.charging_detected

    def is_charging_stopped(self, state):
        """Check if charging has stopped."""
        return not self.charging_detected

    # State entry methods
    def on_enter_reset(self, state):
        """Handle reset state entry."""
        _LOGGER.info("Entering reset state")
        # Stop charging and restore stored amp value

    def on_enter_charge_start_pending(self, state):
        """Handle charge start pending state entry."""
        self.pending_start_time = datetime.now()

    def on_enter_charging_warmup(self, state):
        """Handle charging warmup state entry."""
        # Set a timer for 1 minute
        _LOGGER.info("Starting charging warmup")
        # Set amps and start charging

    def on_enter_stop_charge_pending(self, state):
        """Handle stop charge pending state entry."""
        self.pending_stop_time = datetime.now()

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
