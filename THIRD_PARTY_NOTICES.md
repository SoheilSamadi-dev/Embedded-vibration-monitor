# Third-party notices

## Scope

The root LICENSE applies to original project code, documentation, configuration,
and synthetic example data. It does not change any third-party license. The
standard license text itself retains its original copyright notice.

This project downloads external dependencies to build its Nicla firmware.
They are excluded from version control. This inventory records license evidence
from the locally installed versions; it is not an exhaustive inventory of every
file or binary linked by the board package, or clearance for binary redistribution.

## Firmware dependencies reviewed

| Component | Version | License evidence |
|---|---|---|
| Arduino_BHY2 | 1.0.8 | Its root LICENSE.txt contains GNU AGPL v3. Individual bundled components can have separate notices. |
| Bosch BHY2 sensor API files bundled within Arduino_BHY2 | Bundled copy | Inspected src/bosch source headers contain Bosch Sensortec copyright notices and BSD three-clause terms. |
| ArduinoBLE | 2.1.0 | LICENSE contains LGPL 2.1; inspected source headers permit LGPL 2.1 or later. |
| Arduino Mbed OS Nicla board package | 4.6.0 | Mixed components. Inspected Arduino core and Wire headers permit LGPL 2.1 or later. Do not treat this as a single license for the whole package. |
| Nicla_Sense_System | Supplied by board package 4.6.0; build reports 1.0 | Used by the build. The local inspection did not establish complete licensing terms for all included support files. Retain upstream notices and review the exact source before redistributing those components. |

ArduinoBLE can be a build dependency even though this project uses USB rather
than implementing a BLE transport.

Upstream sources:

- [Arduino_BHY2](https://github.com/arduino-libraries/Arduino_BHY2)
- [Bosch BHY2 Sensor API](https://github.com/boschsensortec/BHY2-Sensor-API)
- [ArduinoBLE](https://github.com/arduino-libraries/ArduinoBLE)
- [ArduinoCore-mbed](https://github.com/arduino/ArduinoCore-mbed)

Arduino_SpiNINA and Arduino_SE05X are also installed in the original local
workspace and contain MPL 2.0 license files. They were not listed as used
libraries in the successful firmware build reviewed here and are not published.

## Tools and runtime

Arduino CLI, the C++ toolchain, Python, Bash, GNU coreutils, systemd, and logrotate
are external build/runtime tools. This repository does not distribute or
relicense them. Telegram is an external service; use remains subject to its terms.

## Distribution notes

Keep third-party copyright and license notices intact when copying their source.
Before distributing compiled firmware or bundled dependencies, review the exact
components included and satisfy their applicable license, notice, and
corresponding-source obligations. A root AGPL license or a link to an upstream
repository is not, by itself, a complete binary-distribution compliance package.

The Python/Linux programs are separate processes communicating with the firmware
through serial data; they are licensed under AGPL v3 here by the project author's
choice, not because this document asserts that serial communication imposes the
firmware library's license on them.
