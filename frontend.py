import asyncio
import aiohttp
import aiohttp.web
import json
import os
import printegration
import regfox
import ssl
import toml

class Frontend:
    def __init__(self, config_file):
        self._config = toml.load(config_file)
        if 'ssl' in self._config['frontend']:
            self._ssl = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self._ssl.load_cert_chain(
                self._config['frontend']['ssl']['ssl_cert'],
                self._config['frontend']['ssl'].get('ssl_key', None),
                self._config['frontend']['ssl'].get('ssl_key_passphrase', None),
            )
            self._ssl.options |= ssl.OP_NO_TLSv1
            self._ssl.options |= ssl.OP_NO_TLSv1_1
        else:
            self._ssl = None

    async def _startup(self):
        self._event_name = self._config['regfox']['event_name']
        self._api = regfox.RegFoxClientSession(api_key=self._config['regfox']['api_key'])
        self._cache = await regfox.RegFoxCache.construct(self._api, self._config['regfox'])
        self._printer = await asyncio.get_event_loop().run_in_executor(None, printegration.Printegration, self._config['printer'])
        self._update_database_task = asyncio.ensure_future(self._update_database())

    @classmethod
    async def construct(cls, *arg, **kw):
        self = cls(*arg, **kw)
        await self._startup()
        return self

    async def close(self):
        self._update_database_task.cancel()
        await self._cache.close()

    async def __aenter__(self):
        await self._startup()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def _update_database(self):
        while True:
            await self._cache.sync()
            await asyncio.sleep(self._config['frontend']['update_period'])

    def add_routes_to_app(self, app):
        app.add_routes([
            aiohttp.web.StaticDef('/static', 'static', {}),
            aiohttp.web.get('/', self.main_page),
            aiohttp.web.get('/query', self.query),
            aiohttp.web.get('/printer_list', self.printer_list),
            aiohttp.web.get('/print_badge', self.print_badge),
            aiohttp.web.get('/print_test', self.print_test),
            aiohttp.web.get('/update_badge', self.update_badge),
            aiohttp.web.get('/checkin_badge', self.checkin_badge),
            aiohttp.web.get('/checkout_badge', self.checkout_badge),
            aiohttp.web.get('/get_api_limits', self.get_api_limits),
        ])

    async def query(self, request):
        try:
            limit = int(request.query.get('limit', 0))
        except ValueError:
            limit = 0

        try:
            offset = int(request.query.get('offset', 0))
        except ValueError:
            offset = 0

        criteria = request.query.get('criteria', '')

        registrants = await self._cache.search_registrants(criteria, limit, offset)
        return aiohttp.web.json_response(registrants, dumps=regfox.JSONEncoder.dumps)

    async def printer_list(self, request):
        printers = await asyncio.get_event_loop().run_in_executor(None, self._printer.printer_list)
        return aiohttp.web.json_response(printers)

    async def print_badge(self, request):
        name = request.query.get('name')
        if name == "null":
            name = None

        id_ = int(request.query.get('id', 0))
        registrant = await self._cache.get_registrant(id_)
        registrant['eventName'] = self._event_name
        await asyncio.get_event_loop().run_in_executor(None, self._printer.print_badge, registrant, name)
        return aiohttp.web.json_response(None)

    async def print_test(self, request):
        name = request.query.get('name')
        slot = request.query.get('slot', '<no slot>')
        if name == "null":
            name = None

        await asyncio.get_event_loop().run_in_executor(None, self._printer.print_test, name, slot)
        return aiohttp.web.json_response(None)

    async def update_badge(self, request):
        id_ = int(request.query.get('id', 0))
        updated_registrant = await self._cache.update_registrant(id_)
        return aiohttp.web.json_response(updated_registrant, dumps=regfox.JSONEncoder.dumps)

    async def checkin_badge(self, request):
        id_ = int(request.query.get('id', 0))
        updated_registrant = await self._cache.checkin_registrant(id_)
        return aiohttp.web.json_response(updated_registrant, dumps=regfox.JSONEncoder.dumps)

    async def checkout_badge(self, request):
        id_ = int(request.query.get('id', 0))
        updated_registrant = await self._cache.checkout_registrant(id_)
        return aiohttp.web.json_response(updated_registrant, dumps=regfox.JSONEncoder.dumps)

    async def main_page(self, request):
        raise aiohttp.web.HTTPFound('/static/index.html')

    async def get_api_limits(self, request):
        return aiohttp.web.json_response(await self._api.get_api_limits(), dumps=regfox.JSONEncoder.dumps)

    async def _app_startup(self, app):
        await self._startup()

    async def _app_shutdown(self, app):
        await self.close()

    @classmethod
    def run_app(cls, *arg, **kw):
        app = aiohttp.web.Application()
        frontend = Frontend(*arg, **kw)
        frontend.add_routes_to_app(app)
        app.on_startup.append(frontend._app_startup)
        app.on_shutdown.append(frontend._app_shutdown)
        aiohttp.web.run_app(app, ssl_context=frontend._ssl, port=frontend._config['frontend']['port'])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--configuration', '-c', type=os.path.realpath, required=True, help='Configuration File')
    args = parser.parse_args()

    Frontend.run_app(args.configuration)
