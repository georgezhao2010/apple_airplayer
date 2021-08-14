import pyatv
import logging
import asyncio
from homeassistant.const import STATE_ON, STATE_OFF
from pyatv.const import DeviceModel, FeatureName, FeatureState

_LOGGER = logging.getLogger(__name__)

_MODEL_LIST = {
    DeviceModel.AirPortExpress: "AirPort Express",
    DeviceModel.AirPortExpressGen2: "AirPort Express Gen2",
    DeviceModel.Gen2: "Apple TV 2",
    DeviceModel.Gen3: "Apple TV 3",
    DeviceModel.Gen4: "Apple TV 4",
    DeviceModel.Gen4K: "Apple TV 4K",
    DeviceModel.AppleTV4KGen2: "Apple TV 4K Gen2",
    DeviceModel.HomePod: "HomePod",
    DeviceModel.HomePodMini: "HomePod Mini",
    DeviceModel.Unknown: "Unknown"
}


class AirPlayDevice:
    def __init__(self, atv: pyatv.conf.AppleTV, event_loop):
        self._event_loop = event_loop
        self._atv_conf = atv
        self._atv_interface = None
        self._support_play_url = False
        self._support_stream_file = False
        self._support_volume = False
        self._support_volume_set = False

    @property
    def name(self) -> str:
        return self._atv_conf.name

    @property
    def identifier(self) -> str:
        return self._atv_conf.identifier.replace(":", "").lower()

    @property
    def address(self) -> str:
        return str(self._atv_conf.address)

    @property
    def model(self) -> str:
        return _MODEL_LIST.get(self._atv_conf.device_info.model, "Unknown")

    @property
    def version(self) -> str:
        return self._atv_conf.device_info.version if self._atv_conf.device_info.version is not None else "Unknown"

    @property
    def manufacturer(self) -> str:
        return "Apple Inc" if self.model != "Unknown" else "Unknown"

    @property
    def state(self) -> str:
        return STATE_OFF if self._atv_interface is None else STATE_ON

    @property
    def support_play_url(self) -> bool:
        return self._support_play_url

    @property
    def support_stream_file(self) -> bool:
        return self._support_stream_file

    @property
    def support_volume(self) -> bool:
        return self._support_volume

    @property
    def support_volume_set(self) -> bool:
        return self._support_volume_set

    @property
    def volume_level(self):
        if self._atv_interface is not None and self._support_volume:
            return self._atv_interface.audio.volume / 100
        else:
            return 0.5

    async def async_open(self):
        if self._atv_interface is None:
            try:
                self._atv_interface = await pyatv.connect(config=self._atv_conf, loop=self._event_loop)
                if self._atv_interface is not None:
                    for k, f in self._atv_interface.features.all_features().items():
                        if k == FeatureName.PlayUrl and f.state == FeatureState.Available:
                            self._support_play_url = True
                        elif k == FeatureName.StreamFile and f.state == FeatureState.Available:
                            self._support_stream_file = True
                        elif k == FeatureName.Volume and f.state == FeatureState.Available:
                            self._support_volume = True
                        elif k == FeatureName.SetVolume and f.state == FeatureState.Available:
                            self._support_volume_set = True


            except Exception as e:
                _LOGGER.error(f"Exception raised in async_open, {e}")

    async def async_close(self):
        if self._atv_interface is not None:
            try:
                self._atv_interface.close()
                self._atv_interface = None
            except Exception as e:
                _LOGGER.error(f"Exception raised in async_close, {e}")

    async def async_play_url(self, url):
        if self._atv_interface is None:
            await self.async_open()
        try:
            await self._atv_interface.stream.play_url(url)
            await asyncio.sleep(1)
        except Exception as e:
            _LOGGER.error(f"Exception raised in async_play_url, {e}")

    async def async_stream_file(self, filename):
        if self._atv_interface is None:
            await self.async_open()
        try:
            await self._atv_interface.stream.stream_file(filename)
            await asyncio.sleep(1)
        except Exception as e:
            _LOGGER.error(f"Exception raised in async_stream_file, {e}")

    async def async_set_volume(self, volume):
        if self._atv_interface is None:
            await self.async_open()
        try:
            if self._support_volume_set:
                await self._atv_interface.audio.set_volume(volume * 100)
            else:
                _LOGGER.error(f"Device is not supports set volume")
        except Exception as e:
            _LOGGER.error(f"Exception raised in async_set_volume, {e}")


class DeviceManager:
    def __init__(self, event_loop):
        self._event_loop = event_loop

    async def async_get_all_devices(self):
        devices = []
        atvs = await pyatv.scan(self._event_loop)
        for atv in atvs:
            device = AirPlayDevice(atv, self._event_loop)
            await device.async_open()
            if device.support_play_url or device.support_stream_file:
                devices.append(device)
            await device.async_close()
        return devices

    async def async_get_device_by_identifier(self, identifier):
        atvs = await pyatv.scan(self._event_loop)
        for atv in atvs:
            if atv.identifier.replace(":", "").lower() == identifier.lower():
                return AirPlayDevice(atv, self._event_loop)
        return None

    async def async_get_device_by_address(self, address):
        atvs = await pyatv.scan(self._event_loop, hosts=[address])
        if len(atvs) > 0:
            atv = atvs[0]
            device = AirPlayDevice(atv, self._event_loop)
            await device.async_open()
            await device.async_close()
            if device.support_play_url or device.support_stream_file:
                return device
        return None
