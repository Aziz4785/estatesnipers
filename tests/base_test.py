import os

from flask_testing import TestCase

from src import app, db
from src.accounts.models import User
from sqlalchemy_utils import database_exists, create_database, drop_database
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

class BaseTestCase(TestCase):
    def create_app(self):
        #return a Flask instance
        app.config.from_object("config.TestingConfig")
        return app

    @classmethod
    def setUp(cls):
        #called before running any test. In this method, we create all the database tables. 
        # Additionally, we also create a user so that we can play with it later.
        # create the database if it doesn't exist
        cls.create_test_user_and_db()

    @classmethod
    def tearDownClass(cls):
        # Drop the test database
        cls.drop_test_db()

    @classmethod
    def create_test_user_and_db(cls):
        # Connect to PostgreSQL
        """
        The dbname='postgres' in that connection string refers to the default PostgreSQL administrative database, 
        not your application's database. 
        It's used to connect to PostgreSQL initially to create new databases and users.
        """
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            host='localhost',
            password='DubaiAnalytics_123'  # Replace with your actual postgres superuser password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Create test user
        try:
            cur.execute("CREATE USER testuser WITH PASSWORD 'testpassword'")
        except psycopg2.Error:
            # If user already exists, ignore the error
            conn.rollback()

        # Create test database
        try:
            cur.execute("CREATE DATABASE test_db OWNER testuser")
        except psycopg2.Error:
            # If database already exists, ignore the error
            conn.rollback()

        cur.close()
        conn.close()

    @classmethod
    def drop_test_db(cls):
        if database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
            drop_database(app.config['SQLALCHEMY_DATABASE_URI'])

    def setUp(self):
        db.create_all()
        user = User(email="ad@min.com", password="admin_user")
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()