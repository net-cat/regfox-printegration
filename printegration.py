import asyncio
import cups
from collections import namedtuple
from mako.template import Template
import io
import os
import toml
import regfox
import badges
from GenericBadge import GenericBadgeTemplate

class Printegration:
    PrinterDef = namedtuple("PrinterDef", ('name', 'info', 'model'))
    def __init__(self, cache, config):
        self._cache = cache
        self._config = config

    async def _startup(self):
        self._cups_connection = await asyncio.get_event_loop().run_in_executor(None, cups.Connection)
        pass

    @classmethod
    async def construct(cls, *arg, **kw):
        self = cls(*arg, **kw)
        await self._startup()
        return self

    async def close(self):
        pass

    async def __aenter__(self):
        await self._startup()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    def _printer_list(self):
        printers = []
        for name, props in self._cups_connection.getPrinters().items():
            printers.append(self.PrinterDef(name, props['printer-info'], props['printer-make-and-model']))
        return printers

    async def printer_list(self):
        return await asyncio.get_event_loop().run_in_executor(None, self._printer_list)

    def _print_png(self, printer, data, job_name='badge', media=None):
        cups_options = {}
        if media is not None:
            cups_options['media'] = media

        job_id = self._cups_connection.createJob(printer, job_name, cups_options)
        self._cups_connection.startDocument(printer, job_id, job_name, cups.CUPS_FORMAT_AUTO, 1)
        self._cups_connection.writeRequestData(data, len(data))
        self._cups_connection.finishDocument(printer)

    async def print_badge(self, registrant_id):
        registrant = await self._cache.get_registrant(registrant_id)
        registrant['eventName'] = self._config['event_name']

        badge_template = GenericBadgeTemplate(default_font=self._config['default_font'])
        png_data = io.BytesIO()
        await asyncio.get_event_loop().run_in_executor(None, badge_template.render, registrant, png_data, 'png')
        await asyncio.get_event_loop().run_in_executor(
            None,
            self._print_png,
            self._config['printer_name'],
            png_data.getvalue(),
            'badge-{}'.format(registrant['registrantId']),
            badge_template.cups_media
        )

async def print_badge(config_file, registrant_id):
    config = toml.load(config_file)
    async with regfox.RegFoxClientSession(api_key=config['regfox']['api_key']) as api:
        async with regfox.RegFoxCache(api, config['regfox']) as cache:
            #await cache.sync()
            async with Printegration(cache, config['printer']) as printer:
                await printer.print_badge(registrant_id)

async def list_printers(config_file):
    config = toml.load(config_file)
    async with regfox.RegFoxClientSession(api_key=config['regfox']['api_key']) as api:
        async with regfox.RegFoxCache(api, config['regfox']) as cache:
            async with Printegration(cache, config['printer']) as printer:
                printers = await printer.printer_list()
                for printer in printers:
                    print('{0.name} (model={0.model}, info={0.info})'.format(printer))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--configuration', '-c', type=os.path.realpath, required=True, help='Configuration File')
    parser.add_argument('--registrant-id', '-i', type=int, required=False, default=None, help="Registrant ID")
    parser.add_argument('--list-printers', '-l', action='store_true', help='Show all available printers.')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    if args.list_printers:
        loop.run_until_complete(list_printers(args.configuration))

    elif args.registrant_id is not None:
        loop.run_until_complete(print_badge(args.configuration, args.registrant_id))
