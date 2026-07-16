import os
import re
from backend import create_app
from backend.extensions import db
from backend.models.user import User
from backend.models.driver import Driver
from backend.models.vehicle import Vehicle
from backend.models.contract import Contract
from backend.models.payment import Payment
from backend.models.expense import Expense
from backend.models.audit import AuditLog

os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_PIJ7Mr1OUzHj@ep-orange-rice-asi2g2sb.c-4.eu-central-1.aws.neon.tech/neondb?sslmode=require'

app = create_app('production')
print('DB URI=', app.config['SQLALCHEMY_DATABASE_URI'])
with app.app_context():
    print('USER COUNT=', User.query.count())
    print('ACTIVE OWNER COUNT=', User.active_owner_count())
    print('DRIVER COUNT=', Driver.query.count())
    print('VEHICLE COUNT=', Vehicle.query.count())
    print('CONTRACT COUNT=', Contract.query.count())
    print('PAYMENT COUNT=', Payment.query.count())
    print('EXPENSE COUNT=', Expense.query.count())
    print('AUDIT LOG COUNT=', AuditLog.query.count())

    client = app.test_client()
    r = client.get('/login')
    html = r.get_data(as_text=True)
    print('/login GET', r.status_code)
    print('Set-Cookie header:', r.headers.get('Set-Cookie'))
    print('Login HTML snippet:', html[:800])
    m = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html)
    print('CSRF token found:', bool(m))
    token = m.group(1) if m else None
    print('Token:', token)
    r2 = client.post('/login', data={'csrf_token': token, 'username': 'owner', 'password': 'owner123'}, follow_redirects=False)
    print('/login POST', r2.status_code)
    print('Location:', r2.headers.get('Location'))
    print('POST body snippet:', r2.get_data(as_text=True)[:800])
