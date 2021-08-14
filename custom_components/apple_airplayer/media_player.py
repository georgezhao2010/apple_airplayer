import logging
import os
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.components.media_player import (
    SUPPORT_PLAY_MEDIA, SUPPORT_VOLUME_STEP, SUPPORT_VOLUME_SET,
    SUPPORT_TURN_ON, SUPPORT_TURN_OFF, SUPPORT_VOLUME_STEP, MediaPlayerEntity
)
from .device_manager import DeviceManager, AirPlayDevice
from .const import DOMAIN, CONF_CACHE_DIR
from homeassistant.const import CONF_DEVICE, CONF_ADDRESS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    identifier = config_entry.data.get(CONF_DEVICE)
    address = config_entry.data.get(CONF_ADDRESS)
    cache_dir = config_entry.data[CONF_CACHE_DIR]
    man = DeviceManager(hass.loop)
    device = None
    if identifier is not None:
        device = await man.async_get_device_by_identifier(identifier)
    elif address is not None:
        device = await man.async_get_device_by_address(address)
    if device is not None:
        await device.async_open()
        async_add_entities([AirPlayer(device, cache_dir)])


class AirPlayer(MediaPlayerEntity):
    def __init__(self, player_device: AirPlayDevice, cache_dir):
        self._player_device = player_device
        self._unique_id = f"{DOMAIN}.airplay_{self._player_device.identifier}"
        self.entity_id = self._unique_id
        self._cache_dir = cache_dir
        self._features = SUPPORT_TURN_ON | SUPPORT_TURN_OFF
        if self._player_device.support_stream_file or self._player_device.support_play_url:
            self._features |= SUPPORT_PLAY_MEDIA
        if self._player_device.support_volume_set:
            self._features |= SUPPORT_VOLUME_SET | SUPPORT_VOLUME_STEP
        self._device_info = {
            "identifiers": {(DOMAIN, self._player_device.identifier)},
            "manufacturer": self._player_device.manufacturer,
            "model": self._player_device.model,
            "sw_version": self._player_device.version,
            "name": self._player_device.name
        }

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._player_device.name

    @property
    def volume_level(self) -> float:
        return self._player_device.volume_level

    @property
    def state(self):
        return self._player_device.state

    @property
    def supported_features(self):
        return self._features

    @property
    def device_info(self):
        return self._device_info

    async def async_set_volume_level(self, volume):
        if 0 <= volume <= 1:
            await self._player_device.async_set_volume(volume)

    async def async_turn_off(self):
        await self._player_device.async_close()

    async def async_turn_on(self):
        await self.hass.async_create_task(self._player_device.async_open())

    async def async_play_media(self, media_type, media_id, **kwargs):
        if self._player_device.support_play_url:
            self.hass.async_create_task(self.async_play_url(media_id))
        elif self._player_device.support_stream_file:
            self.hass.async_create_task(self.async_play_stream(media_id))

    async def async_save_audio_file(self, filename, data):
        def save_audio():
            with open(filename, "wb") as fp:
                fp.write(data)
        await self.hass.async_add_executor_job(save_audio)

    async def async_play_url(self, url):
        try:
            await self._player_device.async_play_url(url)
        except Exception as e:
            _LOGGER.debug(f"Play URL failed {e}")

    async def async_play_stream(self, url) :
        audio_file = url[url.rfind('/') + 1:]
        play = False
        filename = f"{self._cache_dir}/{audio_file}"
        if not os.path.exists(self._cache_dir):
            os.makedirs(self._cache_dir)
        if not os.path.exists(filename):
            _LOGGER.debug(f"File {audio_file} not in cache folder {self._cache_dir}, now downloading")
            session = async_create_clientsession(self.hass)
            r = await session.get(url)
            if r.status == 200:
                audio_data = await r.read()
                _LOGGER.debug(f"{len(audio_data)} bytes downloaded")
                await self.async_save_audio_file(filename, audio_data)
                play = True
        else:
            play = True
        if play:
            _LOGGER.debug(f"File {audio_file} in cache, now playing")
            try:
                await self._player_device.async_stream_file(filename)
            except Exception as e:
                _LOGGER.debug(f"Play stream failed {e}")
