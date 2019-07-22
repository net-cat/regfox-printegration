import asyncio
import aiohttp
import aiosqlite
import pprint
import datetime
import os
import sys
import toml

class RegFoxClientSession(aiohttp.ClientSession):
    def __init__(self, *, api_key=None, service_prefix='https://api.webconnex.com/v2/public', **kw):
        self._service_prefix = service_prefix
        self._api_key = api_key

        if api_key is not None:
            if 'headers' in kw and is_instance(kw, dict):
                kw['headers'] = kw['headers'].copy()
            else:
                kw['headers'] = [('apiKey', str(api_key))]
        super().__init__(**kw)

    async def api_request(self, method, uri, **kw):
        async with self.request(method, self._service_prefix + uri, **kw) as request:
            return await request.json()

    async def api_get(self, uri, **params):
        data_list = []

        while True:
            new_data = await self.api_request('GET', uri, params=params)
            if not isinstance(new_data['data'], list):
                return new_data['data']
            data_list += new_data['data']
            if not new_data.get('hasMore', False):
                break
            params['startingAfter'] = new_data['startingAfter']
        return data_list

    async def search_transactions(self, id_=None, **params):
        uri = '/search/transactions'
        if id_ is not None:
            uri += '/{}'.format(id_)
        return await self.api_get(uri, **params)

    async def search_registrants(self, id_=None, **params):
        uri = '/search/registrants'
        if id_ is not None:
            uri += '/{}'.format(id_)
        return await self.api_get(uri, **params)

    async def search_orders(self, id_=None, **params):
        uri = '/search/orders'
        if id_ is not None:
            uri += '/{}'.format(id_)
        return await self.api_get(uri, **params)

    async def search_customers(self, id_=None, **params):
        uri = '/search/customers'
        if id_ is not None:
            uri += '/{}'.format(id_)
        return await self.api_get(uri, **params)

    async def forms(self, id_=None, **params):
        uri = '/forms'
        if id_ is not None:
            uri += '/{}'.format(id_)
        return await self.api_get(uri, **params)

    async def forms_inventory(self, id_=None, **params):
        uri = '/forms/inventory'
        if id_ is not None:
            uri += '/{}'.format(id_)
        return await self.api_get(uri, **params)

    async def coupons_global(self, **params):
        return await self.api_get('/coupons/global', **params)

    async def coupons_form(self, id_=None, **params):
        uri = '/coupons/form'
        if id_ is not None:
            uri += '/{}'.format(id_)
        return await self.api_get(uri, **params)

    async def coupons(self, id_, **params):
        uri = '/coupons/{}'.format(id_)
        return await self.api_get(uri, **params)

class RegFoxCache:
    def __init__(self, client_session, form_id, database=':memory:'):
        self._client_session = client_session
        self._db_file = database
        self._db = None
        self._form_id = str(form_id)

    async def _startup(self):
        first_sync = self._db_file == ':memory' or not os.path.exists(self._db_file)

        self._db = await aiosqlite.connect(self._db_file)
        await self._db.execute('''
        create table if not exists badges (
            registrantId INT,
            orderId INT,
            badgeLevel TEXT,
            orderStatus TEXT,
            firstName TEXT,
            lastName TEXT,
            email TEXT,
            attendeeBadgeName TEXT,
            dateOfBirth INT,
            phone TEXT,
            checkedIn INT
        )
        ''')
        await self._db.commit()

        if first_sync:
            await self.sync(rebuld=True)

    @classmethod
    async def construct(cls, *args, **kwargs):
        self = cls(*args, **kwargs)
        await self._startup()
        return self

    async def close(self):
        await self._db.close()

    async def __aenter__(self):
        await self._startup()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    @staticmethod
    def list_to_dict(lst, id_field='id'):
        retval = {}
        for item in lst:
            retval[item.get(id_field)] = item
        return retval

    @staticmethod
    def date_from_regfox(incoming_date):
        if incoming_date is None:
            return None
        return datetime.datetime.strptime(incoming_date, "%Y-%m-%d").date()

    @staticmethod
    def date_to_database(date_object):
        if date_object is None:
            return 0
        return date_object.toordinal()

    @staticmethod
    def date_from_database(database_date):
        if database_date == 0:
            return None
        return datetime.date.fromordinal(database_date)

    async def sync(self, *, rebuild=False):
        registrant_params = {}
        order_params = {}
        if not rebuild:
            async with self._db.execute('select max(registrantId), max(orderId) from badges') as cursor:
                registrant_params['startingAfter'], order_params['startingAfter'] = await cursor.fetchone()
        print("REBUILD:", rebuild, registrant_params, order_params)

        registrants, orders = await asyncio.gather(
            self._client_session.search_registrants(formId=self._form_id, **registrant_params),
            self._client_session.search_orders(formId=self._form_id, **order_params),
        )

        #registrant_dict = self.list_to_dict(registrants)
        order_dict = self.list_to_dict(orders)

        inserts = []
        for registrant in registrants:
            REG_OPTION_PATH = 'registrationOptions'

            options = {}
            selected_option = None
            fields = {}
            for datum in registrant['fieldData']:
                if datum['path'] == REG_OPTION_PATH:
                    selected_option = datum['value']
                elif datum['path'].startswith(REG_OPTION_PATH):
                    options[datum['path'][len(REG_OPTION_PATH)+1:]] = datum['label']
                else:
                    fields[datum['path']] = datum['value']

            inserts.append([
                registrant['id'], # registrantId
                registrant['orderId'], # orderId
                options[selected_option], # badgeLevel
                order_dict[registrant['orderId']]['status'], # orderStatus
                fields.get('name.first', None), #registrant['firstName'], # firstName
                fields.get('name.last', None), #registrant['lastName'], # lastName
                fields.get('email', None), # email
                fields.get('attendeeBadgeName', None), # attendeeBadgeName
                self.date_to_database(self.date_from_regfox(fields.get('dateOfBirth', None))), # dateOfBirth
                fields.get('phone', None), # phone
                registrant['checkedIn'] # checkedIn
            ])

        print("ADDED:", len(inserts))

        if rebuild:
            await self._db.execute('delete from badges')

        await self._db.executemany('''
            insert into badges (
                registrantId,
                orderId,
                badgeLevel,
                orderStatus,
                firstName,
                lastName,
                email,
                attendeeBadgeName,
                dateOfBirth,
                phone,
                checkedIn
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', inserts)
        await self._db.commit()

async def main(config_file):
    args = toml.load(config_file)
    async with RegFoxClientSession(api_key=args['api_key']) as api:
        async with RegFoxCache(api, args['form_id'], args['database_file']) as cache:
            await cache.sync(rebuild=False)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--configuration', '-c', type=os.path.realpath, required=True, help='Configuration File')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.configuration))
    loop.close()

