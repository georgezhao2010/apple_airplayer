import logging
from .const import DOMAIN, DEVICES, CONF_CACHE_DIR
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE, CONF_ADDRESS
from .device_manager import DeviceManager
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    available_device = {}

    async def async_step_user(self, user_input=None, error=None):
        if DOMAIN not in self.hass.data:
            self.hass.data[DOMAIN] = {}
        if DEVICES not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN][DEVICES] = []
        if user_input is not None:
            man = DeviceManager(self.hass.loop)
            devices = await man.async_get_all_devices()
            self.available_device = {}
            for device in devices:
                if device.identifier not in self.hass.data[DOMAIN][DEVICES]:
                    self.available_device[device.identifier] = f"{device.name}"
            if len(self.available_device) > 0:
                return await self.async_step_devinfo()
            else:
                return await self.async_step_manually()
        _LOGGER.debug(user_input, error)
        return self.async_show_form(
            step_id="user",
            errors={"base": error} if error else None
        )

    async def async_step_devinfo(self, user_input=None, error=None):
        if user_input is not None:
            return self.async_create_entry(
                title=f"{self.available_device[user_input[CONF_DEVICE]]}",
                data=user_input)
        return self.async_show_form(
            step_id="devinfo",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE, default=sorted(self.available_device.keys())[0]):
                    vol.In(self.available_device),
                vol.Required(CONF_CACHE_DIR, default="/tmp/tts"): str
            }),
            errors={"base": error} if error else None
        )

    async def async_step_manually(self, user_input=None, error=None):
        if user_input is not None:
            man = DeviceManager(self.hass.loop)
            device = await man.async_get_device_by_address(user_input[CONF_ADDRESS])
            if device is not None:
                identifier = device.identifier
                if identifier in self.hass.data[DOMAIN][DEVICES] or \
                        user_input[CONF_ADDRESS] in self.hass.data[DOMAIN][DEVICES]:
                    return await self.async_step_manually(error="device_exist")
                return self.async_create_entry(
                    title=f"{device.name}",
                    data=user_input)
            else:
                return await self.async_step_manually(error="no_devices")

        return self.async_show_form(
            step_id="manually",
            data_schema=vol.Schema({
                vol.Required(CONF_ADDRESS): str,
                vol.Required(CONF_CACHE_DIR, default="/tmp/tts"): str
            }),
            errors={"base": error} if error else None
        )