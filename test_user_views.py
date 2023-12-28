import os

os.environ["DATABASE_URL"] = 'postgresql:///warbler_test'

from unittest import TestCase

from flask import session
from flask_bcrypt import Bcrypt

from app import app, CURR_USER_KEY
from models import db, User, Message, Like

# This is a bit of hack, but don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Don't req CSRF for testing
app.config['WTF_CSRF_ENABLED'] = False

# Make Flask errors be real errors, rather than HTML pages with error info
app.config['TESTING'] = True

db.drop_all()
db.create_all()

bcrypt = Bcrypt()


class UserViewsTestCase(TestCase):
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
            resp = client.get("/users", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_show_user_okay(self):
        """
        Test that a logged in user can access a user's details.
        """

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = client.get(f"/users/{self.u2_id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("TEST: user detail", html)
            self.assertIn("u2", html)

    def test_show_user_unauth(self):
        """
        Test that an anon user can't see a user's details.
        """

        with app.test_client() as client:
            resp = client.get(f"/users/{self.u2_id}", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)


class UserLikeTestCase(UserViewsTestCase):
    def setUp(self):
        super().setUp()
        u3 = User.signup("u3", "u3@email.com", "password", None)
        db.session.add_all([u3])
        db.session.flush()
        m1 = Message(text="text", user_id=self.u2_id)
        db.session.add_all([m1])
        db.session.flush()
        k1 = Like(user_id=self.u2_id, message_id=m1.id)
        db.session.add_all([k1])
        db.session.commit()

        self.u3_id = u3.id
        self.m1_id = m1.id

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.rollback()


    def test_show_user_likes_okay(self):
        """
        Test that a logged in user can access a user's likes.
        """

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = client.get(f"/users/{self.u2_id}/likes")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("TEST: user show_likes.html", html)
            self.assertIn("u2", html)

    def test_show_user_likes_unauth(self):
        """
        Test that an anon user cannot access a user's likes.
        """

        with app.test_client() as client:
            resp = client.get(
                f"/users/{self.u2_id}/likes", 
                follow_redirects=True
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_add_like(self):
        """
        Test liking a message.
        """

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u3_id

            resp = client.post(
                f"/messages/{self.m1_id}/like",
                follow_redirects=True,
                data={
                    "requesting_url": f"/users/{self.u3_id}/likes"
                }
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("TEST: user show_likes.html", html)
            
            likes = Like.query.filter(Like.message_id == self.m1_id, ).all()
            self.assertEqual(len(likes), 2)

    def test_remove_like(self):
        """
        Test removing a like from a message.
        """

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            resp = client.post(
                f"/messages/{self.m1_id}/like/delete",
                follow_redirects=True,
                data={
                    "requesting_url": f"/users/{self.u3_id}/likes"
                }
            )
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("TEST: user show_likes.html", html)
            
            likes = Like.query.filter(Like.message_id == self.m1_id, ).all()
            self.assertEqual(len(likes), 0)


