# Warbler
A Twitter-like multi-page application built with Flask, PostgreSQL, SQLAlchemy, Jinja and WTForms with unit and integration tests.

[Live Demo](https://mattfergoda-warbler.onrender.com/)

## Running the Project Locally
- Create a `.env` file with:
    - A random, secure `SECRET_KEY`.
    - `DATABASE_URL=postgresql:///warbler`
- Next, create a PostgreSQL database called `warbler`. Note that the database name and the name included in `DATABASE_URL` in the `.env` file must match.
- Then generate some dummy data in the database by running: `python3 -m seed`.

## Test Coverage
Current test coverage is around 96%.

To generate a test coverage report:

- Run: `python -m coverage run -m unittest`. 
- Then run: `python -m coverage report` for a report printed to the terminal or `python -m coverage html` for an html report.

## Future Work
- Add more integration tests.
- Refactor to use Flask Blueprints.
- UI tweaks for liking and showing likes.
