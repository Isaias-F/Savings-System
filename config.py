import sys
import pymysql


VONAGE_API_KEY = '123456789'
VONAGE_API_SECRET = 'SECRETHERE'
VONAGE_PHONE_NUMBER = 'PHONEHERE'

try:
    db = pymysql.connect(
        host='localhost',
        user='root',
        password='MYSQLPASS',
        autocommit=True,
        database='DATABASEHERE'
    )
    print('Connected to MySQL')
except pymysql.Error as e:
    print('Error %d: %s' % (e.args[0], e.args[1]))
    sys.exit(1)