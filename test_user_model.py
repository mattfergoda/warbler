"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follow

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


class UserModelTestCase(TestCase):
    """Tests for User model."""

    def setUp(self):
        """Make test data"""

        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

    def tearDown(self):
        """Reset"""
        
        db.session.rollback()

    def test_user_model(self):
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        # Users should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)
        self.assertEqual(len(u1.liked_messages),0)

        self.assertEqual(len(u2.messages), 0)
        self.assertEqual(len(u2.followers), 0)
        self.assertEqual(len(u2.liked_messages),0)

    def test_is_following_and_followed_by(self):
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        # test is following
        self.assertFalse(u1.is_following(u2))

        u1.followers.append(u2)
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
