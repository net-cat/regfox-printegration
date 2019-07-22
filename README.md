# regfox-printegration

Try to make a better at-door printing setup for RegFox. Because who wants 3"x4" badges with a giant freaking QR code on them?

## Parts

### regfox.py

Provides an interface to the RegFox service, as well as caching a bunch of the data to minimize API usage.

Status: Pretty done. Needs cleanup. Might need a few features added.

### frontend.py

Provides a HTTPS server that will allow you to check in and print badges.

Status: Not started.

### printing.py

Handles generating the badges and sending them to the printer.

Status: Not started.

## Notes

This script is for a specific event. I'm happy to take PR's that help make it more generic, but it still has to work for what I'm using it for at the end of the day.

## Requirements

* Python 3.6 or better. 3.5 will *probably* not work. 3.4 and 2.7 will *definitely* not work.
* I highly recommend making making a virtual environment. Fortunately, Python 3 has `venv` built right in now.
* Linux. I have not tested this in Windows at all. No reason it shouldn't work?

## Setup

NOTE: These instructions assume you have some degree of computer knowledge. I will write better ones when the system is closer to completion.

1. Check out the repo and `cd` into it.
2. Create your virtual environment: `python3 -m venv print-env`
3. Activate it: `source print-env/bin/activate`
4. Update basic python packages: `python -m pip -U pip setuptools wheel`
5. Install the requirements: `python -m pip -r requirements.txt`
6. Copy and edit your config file. (Please don't check your API key into the repo.)
7. Run the script: `python regfox.py -c your_config_file.toml`

The script will do what it does. (At the time of this writing, it fetches all your attendees and puts them in a SQLite database.)
