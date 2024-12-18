"""Switch platform for solmate_mocks integration."""

import logging

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the switch platform."""
    async_add_entities([MockChargerSwitch(entry)])


class MockChargerSwitch(SwitchEntity):
    """Switch for mocking fast charge button."""

    _attr_name = "Mock Charger Switch"
    _attr_unique_id = "mock_charger_switch"
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        self._attr_is_on = False
        self._attr_device_info = DeviceInfo(
            name="Solmate Mocks",
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_set_native_value(self, value: bool) -> None:
        """Update the current value."""
        self._attr_is_on = bool(value)
        self.async_write_ha_state()
