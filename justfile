# Show this help message
default:
    just --list --unsorted

# Run the development server
run:
    uv run manage.py runserver

# Make migrations
makemigrations:
    uv run manage.py makemigrations

# Migrate the database
migrate:
    uv run manage.py migrate

# Make automated Django migrations (based on specified version)
django-upgrade:
    git ls-files -z -- '*.py' | xargs -0r uvx django-upgrade 

# Recreate the database and admin account
reset-for-local-development:
    psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS books4books;"
    psql -U postgres -d postgres -c "DROP ROLE IF EXISTS books4books;"
    psql -U postgres -d postgres -c "CREATE ROLE books4books WITH LOGIN PASSWORD 'password';"
    psql -U postgres -d postgres -c "CREATE DATABASE books4books WITH OWNER books4books;"
    psql -U postgres -d books4books -c "GRANT ALL PRIVILEGES ON DATABASE books4books TO books4books;"
    psql -U postgres -d books4books -c "GRANT ALL ON SCHEMA public TO books4books;"
    psql -U postgres -d books4books -c "CREATE EXTENSION postgis;"
    uv run manage.py migrate
    DJANGO_SUPERUSER_PASSWORD=test uv run manage.py createsuperuser --no-input --username=jeremy --email=jeremy@test.com
    uv run manage.py create_user_profile jeremy --city="Ottawa" --latitude=45.4215 --longitude=-75.6972
    uv run manage.py verify_user_email jeremy