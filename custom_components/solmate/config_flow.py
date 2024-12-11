"""Config flow for solmate integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)
from homeassistant.helpers.selector import (
    DeviceSelector,
    DeviceSelectorConfig,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_input(
    handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Validate."""
    return user_input


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("home_consumption_entity"): EntitySelector(
            EntitySelectorConfig(device_class=SensorDeviceClass.POWER)
        ),
        vol.Required("pv_production_entity"): EntitySelector(
            EntitySelectorConfig(device_class=SensorDeviceClass.POWER)
        ),
        vol.Required("home_battery_soc_entity"): EntitySelector(
            EntitySelectorConfig(device_class=SensorDeviceClass.BATTERY)
        ),
        vol.Required("tesla_ble_device"): DeviceSelector(DeviceSelectorConfig()),
        vol.Required("fast_charge_button_entity"): EntitySelector(
            EntitySelectorConfig(domain="binary_sensor")
        ),
        vol.Required("battery_threshold", default=80): NumberSelector(
            NumberSelectorConfig(
                min=0,
                max=100,
                step=1,
                unit_of_measurement="%",
                mode=NumberSelectorMode.SLIDER,
            )
        ),
        vol.Required("power_buffer", default=500): NumberSelector(
            NumberSelectorConfig(
                min=0,
                max=2000,
                unit_of_measurement="W",
                mode=NumberSelectorMode.BOX,
            )
        ),
    }
)

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(
        schema=STEP_USER_DATA_SCHEMA,
        validate_user_input=validate_input,
        # preview="mold_indicator",
    ),
}
OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(
        schema=STEP_USER_DATA_SCHEMA,
        validate_user_input=validate_input,
        # preview="mold_indicator",
    )
}


class SolmateConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config flow for Solmate."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        return "Solmate"
        # return cast(str, options[CONF_NAME])
