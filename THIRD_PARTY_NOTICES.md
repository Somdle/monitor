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
