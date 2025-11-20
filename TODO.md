# TODO: Switch from MySQL to PostgreSQL for Render Deployment

- [x] Update requirements.txt: Replace pymysql and mysql-connector-python with psycopg2-binary
- [x] Update db.py: Change SQLALCHEMY_DATABASE_URL to PostgreSQL format using environment variables
- [x] Install new dependencies
- [x] Test the app locally (critical-path: app starts without errors)
- [ ] Update environment variables on Render for PostgreSQL connection
