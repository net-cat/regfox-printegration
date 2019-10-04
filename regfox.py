import asyncio
import aiohttp
import aiosqlite
from collections import OrderedDict
import pprint
import datetime
import iso8601
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

        self._limit_lock = asyncio.Lock()
        self._burst_limit = 0
        self._burst_remaining = 0
        self._burst_reset = None
        self._daily_limit = 0
        self._daily_remaining = 0
        self._daily_reset = None

        if api_key is not None:
            if 'headers' in kw and is_instance(kw, dict):
                kw['headers'] = kw['headers'].copy()
            else:
                kw['headers'] = [('apiKey', str(api_key))]
        super().__init__(**kw)

    async def api_request(self, method, uri, **kw):
        async with self.request(method, self._service_prefix + uri, **kw) as response:
            data = await response.json()

            async with self._limit_lock:
                self._burst_limit = int(response.headers['X-Burst-Limit'])
                self._burst_remaining = int(response.headers['X-Burst-Remaining'])
                self._burst_reset = datetime.datetime.utcfromtimestamp(int(response.headers['X-Burst-Limit-Reset']))
                self._daily_limit = int(response.headers['X-Daily-Limit'])
                self._daily_remaining = int(response.headers['X-Daily-Remaining'])
                self._daily_reset = datetime.datetime.utcfromtimestamp(int(response.headers['X-Daily-Limit-Reset']))

            return data

    async def get_api_limits(self):
        async with self._limit_lock:
            return {
                    'burst': {
                        'limit': self._burst_limit,
                        'remaining': self._burst_remaining,
                        'reset': self._burst_reset,
                    },
                    'daily': {
                        'limit': self._daily_limit,
                        'remaining': self._daily_remaining,
                        'reset': self._daily_reset,
                    }
            }

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

    async def check_in(self, **params):
        return await self.api_request('POST', '/registrant/check-in', **params)

    async def check_out(self, **params):
        return await self.api_request('POST', '/registrant/check-out', **params)

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
                    checkedIn INT NOT NULL,
                    dateCheckedIn INT
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
    def datetime_from_regfox(incoming_date):
        if incoming_date is None:
            return None
        return iso8601.parse_date(incoming_date)

    @staticmethod
    def datetime_to_database(datetime_object):
        if datetime_object is None:
            return None
        return int(datetime_object.timestamp())

    @staticmethod
    def datetime_from_database(database_date):
        if database_date is None:
            return None
        return datetime.datetime.utcfromtimestamp(database_date)

    @staticmethod
    def calculate_age(dob, now=datetime.date.today()):
        if not dob or now < dob:
            return 0
        age = now.year - dob.year
        if now.month < dob.month or (now.month == dob.month and now.day < dob.day):
            age -= 1
        return age

    def pythonify_row(self, registrant_dict):
        registrant_dict['dateOfBirth'] = self.date_from_database(registrant_dict['dateOfBirth'])
        registrant_dict['ageAtEvent'] = self.calculate_age(registrant_dict['dateOfBirth'], self._start_date)
        registrant_dict['ageNow'] = self.calculate_age(registrant_dict['dateOfBirth'])
        registrant_dict['checkedIn'] = bool(registrant_dict['checkedIn'])
        registrant_dict['dateCheckedIn'] = self.datetime_from_database(registrant_dict['dateCheckedIn'])

    def unpythonify_row(self, registrant_dict):
        registrant_dict['dateOfBirth'] = self.date_to_database(registrant_dict['dateOfBirth'])
        del registrant_dict['ageAtEvent']
        del registrant_dict['ageNow']
        registrant_dict['checkedIn'] = int(registrant_dict['checkedIn'])
        registrant_dict['dateCheckedIn'] = self.datetime_to_database(registrant_dict['dateCheckedIn'])

    def _parse_options(self, registrant):
        fields = {}
        field_labels = {}

        for datum in registrant['fieldData']:
            path = datum['path']
            if '.' in path:
                root, leaf = path.split('.', 1)
                if root in fields:
                    datum['path'] = leaf
                    fields[root] = datum
                else:
                    fields[path] = datum['value']
                    field_labels[path] = datum['label']
            else:
                fields[path] = datum['value']
                field_labels[path] = datum['label']

        return fields, field_labels

    def _regfox_to_database(self, registrant, fields=None, order_dict=None):
        if fields is None:
            fields = self._parse_options(registrant)[0]
        values = OrderedDict()
        values['registrantId'] = registrant['id']
        values['displayId'] = registrant['displayId']
        values['orderId'] = registrant['orderId']
        values['badgeLevel'] = fields['registrationOptions']['label']
        values['status'] = registrant['status']
        values['firstName'] = fields.get('name.first', None)
        values['lastName'] = fields.get('name.last', None)
        values['email'] = fields.get('email', None)
        values['attendeeBadgeName'] = fields.get('attendeeBadgeName', None)
        values['dateOfBirth'] = self.date_to_database(self.date_from_regfox(fields.get('dateOfBirth', None)))
        values['phone'] = fields.get('phone', None)
        if order_dict is not None:
            values['billingCountry'] = order_dict[registrant['orderId']]['billing']['address'].get('country', None)
            values['billingZip'] = order_dict[registrant['orderId']]['billing']['address'].get('postalCode', None)
        values['checkedIn'] = registrant['checkedIn']
        values['dateCheckedIn'] = self.datetime_to_database(self.datetime_from_regfox(registrant.get('dateCheckedIn', None)))
        return values

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
                        registrant_params['greaterThanId'] = str(max_registrant_id)
                    if max_order_id is not None:
                        order_params['greaterThanId'] = str(max_order_id)

            registrants, orders = await asyncio.gather(
                self._client_session.search_registrants(formId=self._form_id, **registrant_params),
                self._client_session.search_orders(formId=self._form_id, **order_params),
            )
            inserts = []
            columns = None
            order_dict = self.list_to_dict(orders)

            for registrant in registrants:
                values = self._regfox_to_database(registrant, None, order_dict)
                if columns is None:
                    columns = list(values.keys())
                inserts.append(list(values.values()))

            print("ADDED:", len(inserts))

            if rebuild:
                await self._db.execute('delete from badges')

            if inserts:
                insert_columns = ', '.join(columns)
                insert_placeholders = ', '.join(['?'] * len(columns))
                await self._db.executemany('insert into badges ({}) values ({})'.format(insert_columns, insert_placeholders), inserts)

            await self._db.commit()

    def registrant_row_to_dict(self, reg):
        reg_dict = dict(reg)
        self.pythonify_row(reg_dict)
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
                return False
            if cursor.rowcount > 1:
                raise RuntimeError('Registrant {} found multiple times. (This should be impossible since that column is the primary key.)'.format(id_))
            return self.registrant_row_to_dict(await cursor.fetchone())

    async def update_registrant(self, id_):
        async with self._db_lock:
            registrant = await self._client_session.search_registrants(id_)
            if not registrant:
                return False

            values = self._regfox_to_database(registrant)
            update_columns = ', '.join(['{}=?'.format(col) for col in list(values.keys())])
            update_substitutions = list(list(values.values()))
            update_substitutions.append(id_)

            async with self._db.execute('update badges set {} where registrantId=?'.format(update_columns), update_substitutions) as cursor:
                if cursor.rowcount == 0:
                    return False
                if cursor.rowcount > 1:
                    raise RuntimeError('Somehow multiple rows were updated. This should be impossible. Rolling back transaction...')

            await self._db.commit()
        return await self.get_registrant(id_)

    def _make_checkin_data_dict(self, id_, time=None):
        data = {}

        if isinstance(id_, int):
            data['id'] = id_
        elif isinstance(id_, str):
            data['displayId'] = id_
        else:
            raise TypeError('id_ should be str for displayId or int for id')

        if time is None:
            data['date'] = datetime.datetime.utcnow().isoformat() + 'Z'
        else:
            data['date'] = time.isoformat() + 'Z'

        return data

    async def checkin_registrant(self, id_, time=None):
        check_in_data = await self._client_session.check_in(json=self._make_checkin_data_dict(id_, time))

        if check_in_data['responseCode'] != 200:
            return False

        async with self._db_lock:
            await self._db.execute(
                '''update badges set dateCheckedIn=?, checkedIn=? where registrantId=?''',
                (
                    self.datetime_to_database(self.datetime_from_regfox(check_in_data['data']['date'])),
                    1,
                    check_in_data['data']['id']
                ))
            await self._db.commit()

        return await self.get_registrant(id_)

    async def _get_badge_type_counts(self, where='', type_column='badgeLevel'):
        async with self._db.execute('select {0} as badgeLevel, COUNT({0}) as badgeLevelCount from badges {1} group by {0}'.format(type_column, where)) as cursor:
            badge_levels = {}
            rows = await cursor.fetchall()
            for row in rows:
                badge_levels[row['badgeLevel']] = row['badgeLevelCount']
            return badge_levels

    async def get_counts(self):
        async with self._db_lock:
            output = {}
            async with self._db.execute('select count(1) from badges where status="completed"') as cursor:
                output['total'] = (await cursor.fetchone())[0]
            async with self._db.execute('select count(1) from badges where status="completed" and checkedIn=1') as cursor:
                output['checked_in'] = (await cursor.fetchone())[0]
            output['total_badge_counts'] = await self._get_badge_type_counts('where status="completed"')
            output['checked_in_badge_counts'] = await self._get_badge_type_counts('where status="completed" and checkedIn=1')
            output['checked_out_badge_counts'] = await self._get_badge_type_counts('where status="completed" and checkedIn=0')
            return output

    async def checkout_registrant(self, id_, time=None):
        # This endpoint appears to not be functional at this time.
        #return await self._client_session.check_out(json=self._make_checkin_data_dict(id_, time))
        return False

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

async def update_registrant(config_file, id_):
    config = toml.load(config_file)
    async with RegFoxClientSession(api_key=config['regfox']['api_key']) as api:
        async with RegFoxCache(api, config['regfox']) as cache:
            await cache.sync()
            pprint.pprint(await cache.update_registrant(id_))

async def check_in(config_file, id_):
    config = toml.load(config_file)
    async with RegFoxClientSession(api_key=config['regfox']['api_key']) as api:
        async with RegFoxCache(api, config['regfox']) as cache:
            await cache.sync()
            pprint.pprint(await cache.checkin_registrant(id_))

async def check_out(config_file, id_):
    config = toml.load(config_file)
    async with RegFoxClientSession(api_key=config['regfox']['api_key']) as api:
        async with RegFoxCache(api, config['regfox']) as cache:
            await cache.sync()
            pprint.pprint(await cache.checkout_registrant(id_))

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
    parser.add_argument('--update-registrant', dest='update_registrant_id', default=None, required=False, type=int, help='Get registrant by registrantId, updating it from the server.')
    parser.add_argument('--check-in', dest='check_in_id', default=None, required=False, type=int, help='Check in user by registrantId.')
    parser.add_argument('--check-out', dest='check_out_id', default=None, required=False, type=int, help='Check out user by registrantId.')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    if args.show_forms:
        loop.run_until_complete(display_form_ids(args.configuration))
    elif args.search_criteria is not None:
        loop.run_until_complete(search_registrants(args.configuration, args.search_criteria))
    elif args.registrant_id is not None:
        loop.run_until_complete(get_registrant(args.configuration, args.registrant_id))
    elif args.update_registrant_id is not None:
        loop.run_until_complete(update_registrant(args.configuration, args.update_registrant_id))
    elif args.check_in_id is not None:
        loop.run_until_complete(check_in(args.configuration, args.check_in_id))
    elif args.check_out_id is not None:
        loop.run_until_complete(check_out(args.configuration, args.check_out_id))
    else:
        loop.run_until_complete(main(args.configuration))
    loop.close()

