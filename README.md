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

1. Check out the repo and `cd` into it.
2. Create your virtual environment: `python3 -m venv print-env`
3. Activate it: `source print-env/bin/activate`
4. Update basic python packages: `python -m pip install -U pip setuptools wheel` (Also overwrite Ubuntu's stupid modifications to pip that break things in venvs.)
5. Install the requirements: `python -m pip install -r requirements.txt`
6. Copy and edit your config file. (Please don't check your API key into the repo. For now, don't use `:memory:` databases.)
7. Pull jQuery into the static folder: `wget https://code.jquery.com/jquery-3.4.1.min.js -Ostatic/jquery.min.js` (3.4.1 is the latest version at the time of this writing.)
8. Run the script to sync the cache: `python regfox.py -c your_config_file.toml`
9. Run the frontend: `python frontend.py -c your_config_file.toml`
10. Browse to http://127.0.0.1:8080/static/index.html

### Notes:

* These instructions assume you have some degree of computer knowledge. I will write better ones when the system is closer to completion.
* Running `regfox.py` will populate your cache.
* Running `frontend.py` will make no attempt to populate your cache.
* Running with a `:memory:` database will probably not work very well. (This is TODO, like a lot of other things.)

