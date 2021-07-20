# Apple AirPlayer

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Home Assistant integration component, make your AirPlay devices as TTS speakers.

# Befor Use
Apple Airplayer component requires [pyatv](https://pyatv.dev/development/) 0.8.1, which is self-contained in the latest version Home Assistant (2021.7.3). You can run `pip list | grep pyqatv` in your Home Assistant container host to check the version of pyatv. If lower than 0.8.1, you should run commands as below to upgrade pyatv.
```
apk update
apk add build-base
pip install --upgrade pyatv
pip install --upgrade attrs
```

# Installtion
Use HACS and Install as a custom repository, or copy all files in custom_components/apple_airplayer from [Latest Release](https://github.com/georgezhao2010/apple_airplayer/releases/latest) to your <Home Assistant config folder>/custom_components/apple_airplayer in Home Assistant manually. Restart HomeAssistant.

# Configuration
Add Apple AirPlayer component in Home Assistant integrations page, it could auto-discover Airplay devices in network. If component can not found any devices, you can specify the IP address to add the device.
  
# Supports Devices
- AirPort Express
- AirPort Express Gen2
- Apple TV 2
- Apple TV 3
- Apple TV 4
- Apple TV 4K
- Apple TV 4K Gen2
- HomePod
- HomePod Mini
- Other AirPlay compatible devices
