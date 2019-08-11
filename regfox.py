import asyncio
import aiohttp
import aiosqlite
import pprint
import datetime
import os
import sys
import toml
import json

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.date):
            return o.isoformat()
        return super().default(o)

    @classmethod
    def dumps(cls, obj, **kw):
        if 'cls' not in kw:
            kw['cls'] = cls
        return json.dumps(obj, **kw)

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
    def __init__(self, client_session, config):
        self._client_session = client_session
        self._db_file = config['database_file']
        self._db = None
        self._form_id = str(config['form_id'])
        self._db_lock = asyncio.Lock()
        self._start_date = self.date_from_regfox(config['start_date'])

    async def _startup(self):
        self._first_sync = self._db_file == ':memory:' or not os.path.exists(self._db_file)

        async with self._db_lock:
            self._db = await aiosqlite.connect(self._db_file)
            self._db.row_factory = aiosqlite.Row
            await self._db.execute('''
                create table if not exists badges (
                    registrantId INT PRIMARY KEY,
                    displayId TEXT NOT NULL UNIQUE,
                    orderId INT NOT NULL,
                    badgeLevel TEXT NOT NULL,
                    status TEXT NOT NULL,
                    firstName TEXT NOT NULL,
                    lastName TEXT NOT NULL,
                    email TEXT NOT NULL,
                    attendeeBadgeName TEXT NOT NULL,
                    dateOfBirth INT NOT NULL,
                    phone TEXT NOT NULL,
                    billingCountry TEXT,
                    billingZip TEXT,
                    checkedIn INT NOT NULL
                )
            ''')
            await self._db.commit()

    @classmethod
    async def construct(cls, *args, **kwargs):
        self = cls(*args, **kwargs)
        await self._startup()
        return self

    async def close(self):
        async with self._db_lock:
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

    @staticmethod
    def calculate_age(dob, now=datetime.date.today()):
        if not dob or now < dob:
            return 0
        age = now.year - dob.year
        if now.month < dob.month or (now.month == dob.month and now.day < dob.day):
            age -= 1
        return age

    def process_age(self, registrant_dict):
        registrant_dict['dateOfBirth'] = self.date_from_database(registrant_dict['dateOfBirth'])
        registrant_dict['ageAtCon'] = self.calculate_age(registrant_dict['dateOfBirth'], self._start_date)
        registrant_dict['ageNow'] = self.calculate_age(registrant_dict['dateOfBirth'])

    def unprocess_age(self, registrant_dict):
        registrant_dict['dateOfBirth'] = self.date_to_database(registrant_dict['dateOfBirth'])
        del registrant_dict['ageAtCon']
        del registrant_dict['ageNow']

    async def sync(self, *, rebuild=False):
        async with self._db_lock:
            registrant_params = {}
            order_params = {}
            if rebuild or self._first_sync:
                self._first_sync = False
                print("REBUILD:", registrant_params)
            else:
                async with self._db.execute('select max(registrantId), max(orderId) from badges') as cursor:
                    (max_registrant_id, max_order_id) = await cursor.fetchone()
                    if max_registrant_id is not None:
                        registrant_params['startingAfter'] = max_registrant_id
                    if max_order_id is not None:
                        order_params['startingAfter'] = max_order_id

            registrants, orders = await asyncio.gather(
                self._client_session.search_registrants(formId=self._form_id, **registrant_params),
                self._client_session.search_orders(formId=self._form_id, **order_params),
            )
            inserts = []

            order_dict = self.list_to_dict(orders)

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
                    registrant['displayId'], # displayId
                    registrant['orderId'], # orderId
                    options[selected_option], # badgeLevel
                    registrant['status'],
                    fields.get('name.first', None), #registrant['firstName'], # firstName
                    fields.get('name.last', None), #registrant['lastName'], # lastName
                    fields.get('email', None), # email
                    fields.get('attendeeBadgeName', None), # attendeeBadgeName
                    self.date_to_database(self.date_from_regfox(fields.get('dateOfBirth', None))), # dateOfBirth
                    fields.get('phone', None), # phone
                    order_dict[registrant['orderId']]['billing']['address'].get('country', None), # billingCountry
                    order_dict[registrant['orderId']]['billing']['address'].get('postalCode', None), # billingZip
                    registrant['checkedIn'] # checkedIn
                ])

            print("ADDED:", len(inserts))

            if rebuild:
                await self._db.execute('delete from badges')

            await self._db.executemany('''
                insert into badges (
                    registrantId,
                    displayId,
                    orderId,
                    badgeLevel,
                    status,
                    firstName,
                    lastName,
                    email,
                    attendeeBadgeName,
                    dateOfBirth,
                    phone,
                    billingCountry,
                    billingZip,
                    checkedIn
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', inserts)
            await self._db.commit()

    def registrant_row_to_dict(self, reg):
        reg_dict = dict(reg)
        self.process_age(reg_dict)
        return reg_dict

    async def search_registrants(self, criteria='', limit=0, offset=0):
        search_columns = ('firstName', 'lastName', 'email', 'attendeeBadgeName', 'phone', 'displayId')

        sql = 'select * from badges where '
        sql += ' or '.join(['{} like ?'.format(column) for column in search_columns])
        if limit:
            sql += ' limit {:d}'.format(limit)
            if offset:
                sql += ' offset {:d}'.format(offset)

        async with self._db.execute(sql, ["%{}%".format(criteria)] * len(search_columns)) as cursor:
            registrants = await cursor.fetchall()
            if not registrants:
                return []
            returning = []
            for reg in registrants:
                returning.append(self.registrant_row_to_dict(reg))
            return returning

    async def get_registrant(self, id_):
        async with self._db.execute('select * from badges where registrantId = ?', [id_]) as cursor:
            if cursor.rowcount == 0:
                raise RuntimeError('Registrant {} not found.'.format(id_))
            if cursor.rowcount > 1:
                raise RuntimeError('Registrant {} found multiple times. (This should be impossible since that column is the primary key.)'.format(id_))
            return self.registrant_row_to_dict(await cursor.fetchone())

async def display_form_ids(config_file):
    config = toml.load(config_file)
    async with RegFoxClientSession(api_key=config['regfox']['api_key']) as api:
        form_data = [{'id': 'Form ID', 'name': 'Form Name'}] + await api.forms()
        for datum in form_data:
            print('{id:7}   {name}'.format(**datum))

async def search_registrants(config_file, criteria):
    config = toml.load(config_file)
    async with RegFoxClientSession(api_key=config['regfox']['api_key']) as api:
        async with RegFoxCache(api, config['regfox']) as cache:
            await cache.sync()
            registrants = await cache.search_registrants(criteria)
            for reg in registrants:
                pprint.pprint(reg)

async def get_registrant(config_file, id_):
    config = toml.load(config_file)
    async with RegFoxClientSession(api_key=config['regfox']['api_key']) as api:
        async with RegFoxCache(api, config['regfox']) as cache:
            await cache.sync()
            pprint.pprint(await cache.get_registrant(id_))

async def main(config_file):
    config = toml.load(config_file)
    async with RegFoxClientSession(api_key=config['regfox']['api_key']) as api:
        async with RegFoxCache(api, config['regfox']) as cache:
            await cache.sync(rebuild=False)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--configuration', '-c', type=os.path.realpath, required=True, help='Configuration File')
    parser.add_argument('--show-forms', action='store_true', help='Show all forms (events) that are accessible with the provided configuration.')
    parser.add_argument('--search-registrants', dest='search_criteria', default=None, required=False, help='Search for registrants with the given criteria.')
    parser.add_argument('--get-registrant', dest='registrant_id', default=None, required=False, type=int, help='Get registrant by registrantId.')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    if args.show_forms:
        loop.run_until_complete(display_form_ids(args.configuration))
    elif args.search_criteria is not None:
        loop.run_until_complete(search_registrants(args.configuration, args.search_criteria))
    elif args.registrant_id is not None:
        loop.run_until_complete(get_registrant(args.configuration, args.registrant_id))
    else:
        loop.run_until_complete(main(args.configuration))
    loop.close()

