"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app


app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        m2 = Message(text="m2-text", user_id=u2.id)
        db.session.add_all([m1, m2])
        db.session.commit()

        self.u1_id = u1.id
        self.m1_id = m1.id
        self.u2_id = u2.id
        self.m2_id = m2.id


class MessageShowViewTestCase(MessageBaseViewTestCase):
    """Test cases for views related to showing a message."""

    def test_show_message(self):
        """Test showing a message"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/messages/{self.m1_id}")
            html = resp.get_data(as_text=True)

            self.assertIn("m1-text", html)
            self.assertIn("u1", html)

class MessageAddViewTestCase(MessageBaseViewTestCase):
    """Test cases for views related to adding messages."""

    def test_add_message(self):
        """Test adding a message"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                "/messages/new", 
                data={"text": "Hello"},
                follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertEqual(
                len(Message.query.filter_by(text="Hello").all()),
                1
            )
            self.assertIn("Hello", html)

    def test_anon_add_message(self):
        """Test adding a message while logged out."""

        with app.test_client() as c:
            resp = c.post(
                "/messages/new",
                data={"text": "hi"},
                follow_redirects=True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

            self.assertEqual(
                len(Message.query.filter_by(text="hi").all()),
                0
            )


class MessageDeleteViewTestCase(MessageBaseViewTestCase):
    """Test cases for views related to deleting messages."""

    def test_delete_message(self):
        """Test deleting message while logged in."""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                f"/messages/{self.m1_id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Message successfully deleted.", html)
            self.assertFalse(Message.query.filter_by(id=self.m1_id).all())

    def test_loggedout_delete_message(self):
        """Test deleting message while logged out."""

        with app.test_client() as c:

            resp = c.post(
                f"/messages/{self.m1_id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)
            self.assertEqual(
                len(Message.query.filter_by(id=self.m1_id).all()),
                1
            )

    def test_delete_other_user_message(self):
        """Test deleting another user's message while logged in."""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Try and delete m2 which belongs to u2.
            resp = c.post(
                f"/messages/{self.m2_id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
            self.assertEqual(
                len(Message.query.filter_by(id=self.m2_id).all()),
                1
            )
