# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from flask_bcrypt import Bcrypt

from models import db, User, Message

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

bcrypt = Bcrypt()


class MessageModelTestCase(TestCase):
    """Tests for Message model."""

    def setUp(self):
        """Make test data"""

        db.session.rollback()
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        db.session.commit()
        self.u1_id = u1.id

        m1 = Message(text="test1",user_id=self.u1_id)

        db.session.add(m1)
        db.session.commit()
        self.m1_id = m1.id

    def tearDown(self):
        """Rollback fouled transactions"""

        db.session.rollback()

    def test_message_model(self):
        """Test Message model relationships."""

        m1 = Message.query.get(self.m1_id)

        self.assertEqual(m1.user, User.query.get(self.u1_id))
        self.assertEqual(m1.text,"test1")
        self.assertTrue(m1.liked_by == [])




