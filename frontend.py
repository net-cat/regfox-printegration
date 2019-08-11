import asyncio
import aiohttp
import aiohttp.web
import json
import os
import regfox
import toml

class Frontend:
    def __init__(self, config_file):
        self._config = toml.load(config_file)

    async def _startup(self):
        self._api = regfox.RegFoxClientSession(api_key=self._config['regfox']['api_key'])
        self._cache = await regfox.RegFoxCache.construct(self._api, self._config['regfox'])

    @classmethod
    async def construct(cls, *arg, **kw):
        self = cls(*arg, **kw)
        await self._startup()
        return self

    async def close(self):
        await self._cache.close()

    async def __aenter__(self):
        await self._startup()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    @classmethod
    async def runner(cls, *arg, **kw):
        app = aiohttp.web.Application()
        frontend = await Frontend.construct(*arg, **kw)
        app.add_routes([
            aiohttp.web.StaticDef('/static', 'static', {}),
            aiohttp.web.get('/', frontend.main_page),
            aiohttp.web.get('/query', frontend.query),
        ])
        return app

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

    async def main_page(self, request):
        return aiohttp.web.Response(text='sup')

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--configuration', '-c', type=os.path.realpath, required=True, help='Configuration File')
    args = parser.parse_args()

    aiohttp.web.run_app(Frontend.runner(args.configuration))
