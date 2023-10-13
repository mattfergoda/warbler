"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation

from models import (db,
                    User,
                    Message,
                    Follow,
                    DEFAULT_HEADER_IMAGE_URL,
                    DEFAULT_IMAGE_URL)

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
        """Rollback fouled transactions"""

        db.session.rollback()

    def test_user_model(self):
        """Test User model relationships for newly created users."""

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
        """Test is_following and followed_by instance methods."""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u2.is_followed_by(u1))

        # Have u1 follow u2.
        u2.followers.append(u1)
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
        self.assertTrue(u2.is_followed_by(u1))

    def test_user_signup_success(self):
        """Test signing up a new user."""

        username = "u3"
        email = "u3@email.com"
        password = "password"

        u3 = User.signup(username, email, password, None)

        db.session.commit()

        u3 = User.query.filter(User.username==username).one_or_none()

        self.assertTrue(u3.username == username)
        self.assertTrue(u3.email == email)
        self.assertTrue(
            bcrypt.check_password_hash(u3.password, password)
            )
        self.assertTrue(u3.image_url == DEFAULT_IMAGE_URL)
        self.assertTrue(u3.header_image_url == DEFAULT_HEADER_IMAGE_URL)
        self.assertTrue(u3.bio == "")
        self.assertTrue(u3.location == "")

    def test_user_signup_fail(self):
        """Test signing up a new user with invalid credentials."""

        invalid_username = "u2" # Username taken
        invalid_email = "u2@email.com" # Email taken

        valid_username = "u3"
        valid_email = "u3@email.com"
        password = "password"

        # Invalid username
        user = User.signup(invalid_username, valid_email, password, None)

        with self.assertRaises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        # Invalid email
        user = User.signup(valid_username, invalid_email, password, None)

        with self.assertRaises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        # Empty username
        user = User.signup(None, valid_email, password, None)

        with self.assertRaises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        # Empty email
        user = User.signup(valid_username, None, password, None)

        with self.assertRaises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        # Empty password
        with self.assertRaises(ValueError):
            user = User.signup(valid_username, valid_email, None, None)




