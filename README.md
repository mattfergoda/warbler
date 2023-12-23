# Warbler
A Twitter-like RESTful multi-page application built with Flask, PostgreSQL, SQLAlchemy, Jinja and WTForms with unit and integration tests.

[Live Demo](warbler.demo.mattfergoda.me)

## Running the Project Locally
- Create a `.env` file with:
    - A random, secure `SECRET_KEY`.
    - `DATABASE_URL=postgresql:///warbler`
- Next, create a PostgreSQL database called `warbler`. Note that the database name and the name included in `DATABASE_URL` in the `.env` file must match.
- Then generate some dummy data in the database by running: `python3 -m seed`.

## Test Coverage
Note that I'm in the process of adding integration tests to improve coverage of routes in `app.py`. Model and form files have 100% coverage.

To generate a test coverage report:

- Run: `python -m coverage run -m unittest`. 
- Then run: `python -m coverage report` for a report printed to the terminal or `python -m coverage html` for an html report.