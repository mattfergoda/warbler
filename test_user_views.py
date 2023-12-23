import os

os.environ["DATABASE_URL"] = 'postgresql:///warbler_test'

from unittest import TestCase

from flask import session
from flask_bcrypt import Bcrypt

from app import app, CURR_USER_KEY
from models import db, User

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

            self.assertEqual(resp.status_code, 200)
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
                },
                follow_redirects=True,
            )

            self.assertEqual(resp.status_code, 200)

            u = User.query.filter(User.username == "u3").one_or_none()

            self.assertEqual(u.email, "u3@email.com")

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

    def test_register_email_taken(self):
        """Test a signup with existing email."""

        with app.test_client() as client:
            resp = client.post(
                "/signup",
                data={
                    "username": "u3",
                    "password": "password",
                    "email": "u1@email.com"
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
                },
                follow_redirects=True,
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("TEST: home.html", html)
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
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("TEST: login.html", html)

    def test_login_following_page(self):
        """
        Test viewing user's following page after following another user and
        logging in.
        """

        with app.test_client() as client:
            # login as u1
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # follow u2
            client.post(f'/users/follow/{self.u2_id}')

            resp = client.get(f"/users/{self.u1_id}/following")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("TEST: following.html", html)
            self.assertIn("u2", html)

    def test_login_followers_page(self):
        """
        Test viewing user's followers page with follower once logged in.
        """

        with app.test_client() as client:
            # login as u2
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            # follow u1
            client.post(f'/users/follow/{self.u1_id}')

            # logout
            client.post('/logout')

            # login as u1
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = client.get(f"/users/{self.u1_id}/followers")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("TEST: followers.html", html)
            self.assertIn("u2", html)

    def test_logged_out_follower(self):
        """
        Test that logged out user can't view another user's followers page.
        """

        with app.test_client() as client:
            resp = client.get(
                f"/users/{self.u2_id}/followers",
                follow_redirects=True
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_logged_out_following(self):
        """
        Test that logged out user can't view another user's following page.
        """

        with app.test_client() as client:
            resp = client.get(
                f"/users/{self.u2_id}/following",
                follow_redirects=True
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_list_users_okay(self):
        """
        Test that logged in user can see list of users.
        """

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            #test viewing following page
            resp = client.get("/users")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("u1", html)
            self.assertIn("u2", html)

    def test_list_users_search(self):
        """
        Test that logged in user can search among list of users.
        """

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            #test viewing following page
            resp = client.get("/users?q=u1")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("u1", html)
            self.assertNotIn("u2", html)

    def test_list_users_unauth(self):
        """
        Test that an anon user can't access list users route.
        """

        with app.test_client() as client:

            #test viewing following page
            resp = client.get("/users", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)