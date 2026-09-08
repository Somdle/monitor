# Third-party notices

monitor35 depends on smartscreen-driver 0.2.3 by Hugo Chargois:
https://github.com/hchargois/smartscreen-driver

Its display drivers originate from turing-smart-screen-python:
Copyright (C) 2021-2023 Matthieu Houdebine.
https://github.com/mathoudebine/turing-smart-screen-python

The driver's source headers specify GNU GPL version 3 or, at your option, any later version.
This project uses the driver as a dependency and subclasses it to provide bounded I/O.
No vendor firmware or UsbMonitor binary/theme assets are included.

Other runtime dependencies: Pillow (HPND), NumPy (BSD-3-Clause), psutil (BSD-3-Clause),
pySerial (BSD). Their distributions include their respective notices.
# Optional CPU temperature sensor

LibreHardwareMonitor 0.9.6 is used unmodified from its official release for CPU
temperature acquisition (MPL-2.0, with upstream third-party notices).
Source and license: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/tree/v0.9.6
It is downloaded into .venv/hardware by setup-temperature.ps1 and is not committed.
Official release SHA-256: 086d9f1b5a99e643edc2cfaaac16051685b551e4c5ac0b32a57c58c0e529c001.
The upstream bundled PawnIO installer requires separate administrator authorization;
no driver is automatically installed by Monitor35 or its setup scripts.

Tray integration: pystray 0.19.5 (LGPL-3.0), used unmodified as a dependency.
Source and license: https://github.com/moses-palmer/pystray/tree/v0.19.5
Its dependency six is MIT licensed; distributions include their notices.
