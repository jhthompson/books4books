# Show this help message
default:
    just --list --unsorted

# Run the development server
run:
    uv run manage.py runserver 0.0.0.0:8000

# Make migrations
makemigrations:
    uv run manage.py makemigrations

# Migrate the database
migrate:
    uv run manage.py migrate

# Make automated Django migrations (based on specified version)
django-upgrade:
    git ls-files -z -- '*.py' | xargs -0r uvx django-upgrade 

# Recreate the database and load local sample data
reset-for-local-development:
    psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS books4books;"
    psql -U postgres -d postgres -c "DROP ROLE IF EXISTS books4books;"
    psql -U postgres -d postgres -c "CREATE ROLE books4books WITH LOGIN PASSWORD 'password';"
    psql -U postgres -d postgres -c "CREATE DATABASE books4books WITH OWNER books4books;"
    psql -U postgres -d books4books -c "GRANT ALL PRIVILEGES ON DATABASE books4books TO books4books;"
    psql -U postgres -d books4books -c "GRANT ALL ON SCHEMA public TO books4books;"
    uv run manage.py migrate
    uv run manage.py reset_database
