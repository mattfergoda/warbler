import os

os.environ["DATABASE_URL"] = 'postgresql:///warbler_test'

from unittest import TestCase

from flask import session
from flask_bcrypt import Bcrypt

from app import app, CURR_USER_KEY
from models import db, User, Message

# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Don't req CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

db.drop_all()
db.create_all()

bcrypt = Bcrypt()


class UserRoutesTestCase(TestCase):
    """Tests for User routes."""

    def setUp(self):
        """Make demo data."""

        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()

    def test_get_signup(self):
        """ Test user signup GET request."""

        with app.test_client() as client:
            resp = client.get("/signup")
            html = resp.get_data(as_text=True)

            # TODO: Test status code too (always do this for integration tests)

            self.assertIn("TEST: signup.html", html)


    def test_post_signup_ok(self):
        """Test a valid signup."""

        with app.test_client() as client:
            resp = client.post(
                "/signup",
                data={
                    "username": "u3",
                    "password": "password",
                    "email": "u3@email.com"
                }
            )

            #TODO: Just follow redirect here.
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")

            u = User.query.filter(User.username == "u3").one_or_none()
            # TODO: Don't need to test this here, can test this with models tests.
            self.assertTrue(bcrypt.check_password_hash(u.password, "password"))

            self.assertEqual(u.email, "u3@email.com")

    # TODO: Could also test for case where email is taken.
    def test_register_username_taken(self):
        """Test a signup with existing username."""

        with app.test_client() as client:
            resp = client.post(
                "/signup",
                data={
                    "username": "u1",
                    "password": "password",
                    "email": "u3@email.com"
                }
            )
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Username or email already taken", html)

    def test_post_login_ok(self):
        """
        Test valid login POST.
        """

        with app.test_client() as client:
            resp = client.post(
                "/login",
                data={
                    "username": "u1",
                    "password": "password",
                }
            )
            # TODO: Follow redirect and check for 200 status code and for
            # something on that page.
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "/")
            self.assertEqual(session.get(CURR_USER_KEY), self.u1_id)

    def test_post_login_bad(self):
        """
        Test bad login POST.
        """

        with app.test_client() as client:
            resp = client.post(
                "/login",
                data={
                    "username": "u1",
                    "password": "foofoo",
                },
                follow_redirects=True
            )

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(session.get(CURR_USER_KEY), None)
            self.assertIn("Invalid credentials.", html)

    def test_login_form(self):
        """Test getting the login form."""

        with app.test_client() as client:
            resp = client.get("/login")
            html = resp.get_data(as_text=True)
            # TODO: Test status code too.
            self.assertIn("TEST: login.html", html)

    # TODO: Break this up into two tests. Also test if users following/being followed
    # show up on page.
    def test_login_follower_following(self):
        """
        Test viewing another user's follower and following pages
        once logged in.
        """

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = client.get(f"/users/{self.u2_id}/following")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("TEST: following.html", html)

            resp = client.get(f"/users/{self.u2_id}/followers")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("TEST: followers.html", html)



    def test_logged_out_follower_following(self):
        """
        Test that logged out user can't view another user's follower and
        following pages.
        """

        with app.test_client() as client:

            #test viewing following page
            resp = client.get(
                f"/users/{self.u2_id}/following",
                follow_redirects=True
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

            #test viewing followers page
            resp = client.get(
                f"/users/{self.u2_id}/followers",
                follow_redirects=True
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

