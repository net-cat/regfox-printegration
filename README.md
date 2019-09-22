# regfox-printegration

Try to make a better at-door printing setup for RegFox. Because who wants 3"x4" badges with a giant freaking QR code on them?

## Parts

### regfox.py

Provides an interface to the RegFox service, as well as caching a bunch of the data to minimize API usage.

Status: Pretty done. Needs cleanup. Might need a few features added.

### frontend.py

Provides a HTTPS server that will allow you to check in and print badges.

Status: Needs all the business logic and a bunch of stuff plumbed together. Also the "S" part of HTTPS.

### printegration.py

Handles generating the badges and sending them to the printer.

Status: Basically done.

## Notes

This script is for a specific event. I'm happy to take PR's that help make it more generic, but it still has to work for what I'm using it for at the end of the day.

## Requirements

* Python 3.6 or better. 3.5 will *probably* not work. 3.4 and 2.7 will *definitely* not work.
* I highly recommend making making a virtual environment. Fortunately, Python 3 has `venv` built right in now in many distributions.
* Linux. I have not tested this in Windows at all. No reason it shouldn't work?

## Raspberry Pi/Debian/Ubuntu Installation

1. Use Raspbian Buster, Debian 10, Ubuntu 18.04 or newer. It must ship with Python 3.6 or better.
2. Updates. `sudo apt update && sudo apt upgrade`
3. Install prerequisites: `sudo apt install cups libcups2-dev python3-dev build-essential python3-venv git`
4. Install any required print drivers.
    * For Dymo Label Printers: `sudo apt install printer-driver-dymo`
    * For Brother Label Printers, install the deb file from their site. Example: `dpkg -i ql720nwpdrv-2.1.4-0.armhf.deb`
5. Set your root password. (You will need it to manage CUPS through the web interface.) `sudo passwd root`
6. Set up your printers in CUPS. (This can be through the web interface, CLI interface or through your window manager.)
    * The CUPS web interface is https://127.0.0.1:631 by default.

## Setup

1. Check out the repo and `cd` into it.
2. Create your virtual environment: `python3 -m venv print-env`
3. Activate it: `source print-env/bin/activate`
4. Update basic python packages: `python -m pip install -U pip setuptools wheel` (Also overwrite Ubuntu's stupid modifications to pip that break things in venvs.)
5. Install the requirements: `python -m pip install -r requirements.txt`
    * Please note that the version of `pycups` in the Ubuntu/Debian repos will NOT work. You must let pip build and install the latest version. (That's why you had to install `build-essential`)
6. Copy and edit your config file. (Please don't check your API key into the repo.)
7. Pull jQuery into the static folder: `wget https://code.jquery.com/jquery-3.4.1.min.js -Ostatic/jquery.min.js` (3.4.1 is the latest version at the time of this writing.)
8. Pull JsRender into the static folder: `wget https://www.jsviews.com/download/jsrender.min.js -Ostatic/jsrender.min.js`
9. Run the frontend: `python frontend.py -c your_config_file.toml`
10. Browse to http://127.0.0.1:8080/static/index.html

### Notes:

* These instructions assume you have some degree of computer knowledge. I will write better ones when the system is closer to completion.

# License

This software is Copyright (c) 2019 [net-cat](https://github.com/net-cat) and is distributed under the GNU General Public License version 3.0

The `LiberationSansNarrow-Regular.ttf` font is Copyright (c) 2012 Red Hat, Inc and is distributed under the SIL Open Font License.
