import os


DB_USER = os.getenv('POSTGRES_USER')
DB_PW = os.getenv('POSTGRES_PASSWORD')
DB_NAME = os.getenv('POSTGRES_DB')
DB_HOST = os.getenv('POSTGRES_HOST')
DB_PORT = os.getenv('POSTGRES_PORT')


def db_conn_args():
    return {'dbname': DB_NAME, 'user': DB_USER, 'password': DB_PW, 'host': DB_HOST, 'port': DB_PORT}
