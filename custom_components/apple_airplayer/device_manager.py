import pyatv
try:
    from homeassistent.const import STATE_ON, STATE_OFF
except ImportError:
    STATE_ON = "on"
    STATE_OFF = "off"
from pyatv.const import DeviceModel, FeatureName, FeatureState, DeviceState

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
    def volume_level(self):
        if self._atv_interface is not None:
            return self._atv_interface.audio.volume / 100
        else:
            return 0.5

    async def async_set_volume_level(self, volume):
        if self._atv_interface is not None and 0 <= volume <= 1:
            await self._atv_interface.audio.set_volume(volume * 100)

    async def async_open(self):
        self._atv_interface = await pyatv.connect(config=self._atv_conf, loop=self._event_loop)
        if self._atv_interface is not None:
            for k, f in self._atv_interface.features.all_features().items():
                if k == FeatureName.PlayUrl and f.state == FeatureState.Available:
                    self._support_play_url = True
                elif k == FeatureName.StreamFile and f.state == FeatureState.Available:
                    self._support_stream_file = True

    async def async_close(self):
        if self._atv_interface is not None:
            self._atv_interface.close()
            self._atv_interface = None
            pass

    async def async_play_url(self, url):
        if self._atv_interface is not None:
            await self._atv_interface.stream.play_url(url)

    async def async_stream_file(self, filename):
        if self._atv_interface is not None:
            await self._atv_interface.stream.stream_file(filename)

    async def async_set_volume(self, volume):
        if self._atv_interface is not None:
            await self._atv_interface.audio.set_volume(volume * 100)


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

    async def async_get_device(self, identifier):
        atvs = await pyatv.scan(self._event_loop)
        for atv in atvs:
            if atv.identifier.replace(":", "").lower() == identifier.lower():
                return AirPlayDevice(atv, self._event_loop)
        return None
