import logging
from .const import DOMAIN, DEVICES, CONF_CACHE_DIR
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE
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
                return await self.async_step_user(error="no_devices")
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
