from .const import DOMAIN, DEVICES
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_DEVICE

async def async_setup(hass: HomeAssistant, hass_config: dict):
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry):
    identifier = config_entry.data[CONF_DEVICE]
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if DEVICES not in hass.data[DOMAIN]:
        hass.data[DOMAIN][DEVICES] = []
    hass.data[DOMAIN][DEVICES].append(identifier)
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(
        config_entry, "media_player"))
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry):
    identifier = config_entry.data[CONF_DEVICE]
    hass.data[DOMAIN][DEVICES].remove(identifier)
    await hass.config_entries.async_forward_entry_unload(config_entry, "media_player")
    return True
