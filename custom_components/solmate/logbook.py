"""Describe logbook events."""

from collections.abc import Callable
import logging
from typing import Any

from homeassistant.components.logbook import (
    LOGBOOK_ENTRY_ENTITY_ID,
    LOGBOOK_ENTRY_MESSAGE,
    LOGBOOK_ENTRY_NAME,
)
from homeassistant.core import Event, HomeAssistant, callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@callback
def async_describe_events(
    hass: HomeAssistant,
    async_describe_event: Callable[[str, str, Callable[[Event], dict[str, str]]], None],
) -> None:
    """Describe logbook events."""

    _LOGGER.info("Async_describe_events called")

    @callback
    def async_describe_logbook_event(event: Event) -> dict[str, Any]:
        """Describe a logbook event."""
        data = event.data
        _LOGGER.info("async_describe_logbook_event %s", event)

        # if entity_id := data["request"].get("entity_id"):
        #     state = hass.states.get(entity_id)
        #     name = state.name if state else entity_id
        #     message = (
        #         "sent command"
        #         f" {data['request']['namespace']}/{data['request']['name']} for {name}"
        #     )
        # else:
        #     message = (
        #         f"sent command {data['request']['namespace']}/{data['request']['name']}"
        #     )

        return {
            LOGBOOK_ENTRY_NAME: "Solmate",
            LOGBOOK_ENTRY_MESSAGE: "hello world",
            LOGBOOK_ENTRY_ENTITY_ID: data["request"].get("entity_id"),
        }

    async_describe_event(
        DOMAIN, "solmate_state_changed_event", async_describe_logbook_event
    )
