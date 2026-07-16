import os
import re

os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_PIJ7Mr1OUzHj@ep-orange-rice-asi2g2sb.c-4.eu-central-1.aws.neon.tech/neondb?sslmode=require'

from backend import create_app
from backend.extensions import db
from backend.models.user import User
from backend.models.driver import Driver
from backend.models.vehicle import Vehicle
from backend.models.contract import Contract
from backend.models.payment import Payment
from backend.models.expense import Expense
from backend.models.audit import AuditLog

LOGIN_TOKEN_RE = re.compile(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']')


def extract_csrf(response):
    html = response.get_data(as_text=True)
    match = LOGIN_TOKEN_RE.search(html)
    if not match:
        raise RuntimeError('Unable to extract CSRF token from response')
    return match.group(1)


def login(client, username, password):
    login_page = client.get('/login')
    print('/login GET', login_page.status_code)
    token = extract_csrf(login_page)
    print('CSRF token length:', len(token))
    response = client.post(
        '/login',
        data={
            'csrf_token': token,
            'username': username,
            'password': password,
        },
        follow_redirects=False,
    )
    return response


app = create_app('production')
print('SQLALCHEMY_DATABASE_URI=', app.config['SQLALCHEMY_DATABASE_URI'])
with app.app_context():
    inspector = db.inspect(db.engine)
    print('TABLES=', sorted(inspector.get_table_names()))
    print('USER COUNT=', User.query.count())
    print('ACTIVE OWNER COUNT=', User.active_owner_count())
    print('DRIVER COUNT=', Driver.query.count())
    print('VEHICLE COUNT=', Vehicle.query.count())
    print('CONTRACT COUNT=', Contract.query.count())
    print('PAYMENT COUNT=', Payment.query.count())
    print('EXPENSE COUNT=', Expense.query.count())
    print('AUDIT LOG COUNT=', AuditLog.query.count())

    client = app.test_client()
    owner_response = login(client, 'owner', 'owner123')
    print('/login owner POST', owner_response.status_code, owner_response.headers.get('Location'))

    if owner_response.status_code == 302:
        for path in [
            '/', '/admin/', '/drivers/', '/vehicles/', '/contracts/',
            '/payments/', '/expenses/', '/reports/', '/backup/',
            '/audit-log/', '/settings/',
        ]:
            r = client.get(path)
            print(f'{path} GET', r.status_code)
        logout_response = client.get('/logout', follow_redirects=False)
        print('/logout GET', logout_response.status_code)

    dev_response = login(client, 'developer', 'dev123')
    print('/login developer POST', dev_response.status_code, dev_response.headers.get('Location'))
    if dev_response.status_code == 302:
        for path in ['/developer/', '/admin/', '/']:
            r = client.get(path)
            print(f'{path} GET', r.status_code)
