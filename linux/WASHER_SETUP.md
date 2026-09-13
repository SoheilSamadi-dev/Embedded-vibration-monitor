# Build and run

These instructions describe a fresh installation. The existing project Pi already
has firmware and services installed; preparing this repository does not update it.
The repository folder is `Embedded-vibration-monitor`. The Pi runtime directory
remains `~/embedded-condition-monitor` to match the Python defaults and services.

## Prerequisites — complete these before starting

This guide assumes you have already:

- Obtained an Arduino Nicla Sense ME, a Raspberry Pi 3 Model B, a microSD card,
  a suitable Pi power supply, and a USB data cable for the Nicla.
- Installed Raspberry Pi OS 64-bit on the microSD card, booted the Pi, and
  completed its initial user and network setup.
- Created or selected a Pi account with `sudo` access and know its username and
  the Pi's hostname or IP address.
- Enabled SSH on the Pi and verified that you can log in from your development
  computer. The computer and Pi must have a working network connection between
  them. Replace `YOUR_USER@YOUR_PI` throughout this guide with your actual login.
- Prepared a development computer with a terminal, `ssh`, and `scp`. Commands
  use a macOS/Linux-style shell; this project was developed on macOS.
- Installed Arduino CLI and made `arduino-cli` available in your terminal. The
  commands below install the required board package and sensor library.
- Downloaded or cloned this repository onto the development computer. Run the
  development-computer commands from its root folder, `Embedded-vibration-monitor`.
- Made Python 3 available on the Pi, along with Bash, GNU coreutils (`stty`,
  `tail`, and `date`), systemd, and logrotate. Python 3 is also required on the
  development computer if you want to run the unit tests there.
- Provided internet access on the development computer for Arduino dependency
  downloads and on the Pi if you want Telegram notifications. For notifications,
  you also need a Telegram account and access to a Telegram client.

Basic OS installation, networking, SSH setup, and Arduino CLI installation are
outside this guide. It assumes you can enter terminal commands and edit a text
file. Creating the Telegram bot, installing this project's firmware and Linux
files, configuring the device path, and starting its services are covered below.
No prior installation of this project's code is required.

## 1. Build firmware on the development computer

With Arduino CLI installed, install the board package and library versions used
by this project. From the repository root:

```bash
arduino-cli core update-index
arduino-cli core install arduino:mbed_nicla@4.6.0
arduino-cli lib install 'Arduino_BHY2@1.0.8'
arduino-cli compile --fqbn arduino:mbed_nicla:nicla_sense --build-path build/03_usb_vibration nicla-firmware/03_usb_vibration
arduino-cli board list
```

Connect Nicla over USB. Replace `PORT` below with its listed port:

```bash
arduino-cli upload --fqbn arduino:mbed_nicla:nicla_sense --port PORT --input-dir build/03_usb_vibration
```

If moving an already connected Nicla from the Pi, stop both services before
unplugging it. Reconnect it to the Pi after uploading. The detector requires the
`03_usb_vibration` firmware supplied in this repository.

The original development workspace has an ignored `arduino-cli.yaml` and local
`tools/bin/arduino-cli`. To use that existing toolchain, substitute that executable
and add `--config-file arduino-cli.yaml` to each command. The local config was
updated for the renamed project folder.

## 2. Copy the Linux files to the Pi

Use a Raspberry Pi OS user with sudo access. Substitute its user and host for
`YOUR_USER@YOUR_PI` in these development-computer commands:

```bash
ssh YOUR_USER@YOUR_PI 'mkdir -p ~/embedded-condition-monitor'
scp linux/*.py linux/*.json linux/*.sh linux/*.service linux/*.logrotate linux/logger.env.example YOUR_USER@YOUR_PI:~/embedded-condition-monitor/
```

## 3. Configure the serial logger on the Pi

Identify the stable Nicla device link:

```bash
ls -l /dev/serial/by-id/
mkdir -p ~/.config/condition-monitor
cp ~/embedded-condition-monitor/logger.env.example ~/.config/condition-monitor/logger.env
nano ~/.config/condition-monitor/logger.env
```

Replace the example device path with the actual `/dev/serial/by-id/...` path.
Only the logger should open this port. The sample services grant `dialout` access.

In both copied service files and the logrotate file, replace every `YOUR_USER`
with your Linux username. If its home directory is not `/home/YOUR_USER`, also
adjust the paths and `HOME` values accordingly.

```bash
nano ~/embedded-condition-monitor/nicla-logger.service
nano ~/embedded-condition-monitor/washer-monitor.service
nano ~/embedded-condition-monitor/embedded-condition-monitor.logrotate
```

The service files are templates, not ready to install without these edits.

## 4. Configure optional Telegram delivery

Create a bot using Telegram's verified BotFather, open the bot, and send `/start`.
On the Pi, run:

```bash
python3 ~/embedded-condition-monitor/telegram_notify.py
```

The helper prompts for the token without displaying it and lets you select your
private chat. It saves credentials outside the repository at
`~/.config/condition-monitor/telegram.json` with mode `0600`.
An explicit test sends a message to that chat:

```bash
python3 ~/embedded-condition-monitor/telegram_notify.py --test
```

Without a credentials file the detector records states but disables delivery.
See the [Telegram tutorial](https://core.telegram.org/bots/tutorial) for bot setup.

## 5. Install and start services

On the Pi, after editing the templates:

```bash
sudo cp ~/embedded-condition-monitor/nicla-logger.service /etc/systemd/system/
sudo cp ~/embedded-condition-monitor/washer-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nicla-logger
```

Inspect the latest readings before starting detection:

```bash
tail -n 20 ~/embedded-condition-monitor/nicla-timestamped.log
```

Expect timestamped `VIB_RAW` summaries approximately once per second, typically
about 50 sample pairs per summary. Then start detection:

```bash
sudo systemctl enable --now washer-monitor
journalctl -u washer-monitor -n 20 --no-pager
```

Startup is `UNKNOWN`. Sustained activity requires a complete 20-second window;
initial idle requires 120 quiet seconds. Hand motion can check the pipeline but
does not validate an appliance threshold. Keep mounting consistent between washes.

## 6. Storage and operation

Install the edited rotation configuration:

```bash
sudo cp ~/embedded-condition-monitor/embedded-condition-monitor.logrotate /etc/logrotate.d/embedded-condition-monitor
```

It requests rotation above 10 MB when logrotate runs, with three compressed
archives. `copytruncate` may lose lines. Journal storage and persistence are
separate system settings; this configuration does not preserve previous boots.
Export useful journal entries before shutting down:

```bash
journalctl -u washer-monitor --since today --no-pager > ~/embedded-condition-monitor/washer-cycle-journal.txt
```

Pause or resume both services:

```bash
sudo systemctl stop washer-monitor nicla-logger
sudo systemctl start nicla-logger washer-monitor
```

Stopping does not disable startup at the next boot. To disable automatic startup,
use `sudo systemctl disable --now washer-monitor nicla-logger`.

Edit `~/embedded-condition-monitor/washer-config.json` and restart
`washer-monitor` to apply settings. Capture actual wash times and review data
before tuning. For power-off, use `sudo shutdown -h now` and wait for shutdown
before disconnecting power.

For a guided check of the live readings before a wash, see the
[live sensor check](../docs/SENSOR_CHECK.md).
