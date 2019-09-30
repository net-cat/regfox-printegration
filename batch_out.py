import argparse
import asyncio
import os
import printegration
import regfox
import toml

async def main(config_file, confirm_count, printer):
    config = toml.load(config_file)
    event_name = config['regfox']['event_name']
    async with regfox.RegFoxClientSession(api_key=config['regfox']['api_key']) as api:
        async with regfox.RegFoxCache(api, config['regfox']) as cache:
            printer = printegration.Printegration(printer or config['printer'])

            registrants = await cache.search_registrants()

            if confirm_count == len(registrants):
                for registrant in registrants:
                    template_data = {'eventName': event_name}
                    template_data.update(registrant)
                    printer.print_badge(template_data)
            else:
                print('There are {0} badges. If you want to print them, add the option "--confirm-count {0}"'.format(len(registrants)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--configuration', '-c', type=os.path.realpath, required=True, help='Configuration File')
    parser.add_argument('--confirm-count', type=int, default=None, required=False, help='Used to make sure you want to spit out a lot of labels.')
    parser.add_argument('--printer', default=None, required=False, help='Specify the CUPS printer to use. (Default in config file is used if not specified.)')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.configuration, args.confirm_count, args.printer))
