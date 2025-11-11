"""Config flow for Qustodio integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, LOGIN_RESULT_OK, LOGIN_RESULT_UNAUTHORIZED
from .qustodioapi import QustodioApi

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    api = QustodioApi(data[CONF_USERNAME], data[CONF_PASSWORD])
    
    result = await api.login()
    
    if result == LOGIN_RESULT_UNAUTHORIZED:
        raise InvalidAuth
    elif result != LOGIN_RESULT_OK:
        raise CannotConnect

    # Get profiles to store in config entry
    try:
        profiles = await api.get_data()
        if not profiles:
            _LOGGER.warning("No profiles found for account")
    except Exception as err:
        _LOGGER.error("Failed to get profiles: %s", err)
        raise CannotConnect
    
    # Return info that you want to store in the config entry.
    return {
        "title": f"Qustodio ({data[CONF_USERNAME]})",
        "profiles": profiles,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Qustodio."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Store the profiles data in the config entry
                user_input["profiles"] = info["profiles"]
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""