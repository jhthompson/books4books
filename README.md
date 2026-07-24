# Books4Books

Trade books nearby.

## Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL
- [uv](https://docs.astral.sh/uv/) package manager
- [just](https://github.com/casey/just) command runner

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jhthompson/book-swap.git
   cd book-swap
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up the database (creates PostgreSQL database, runs migrations, and creates a test admin user):
   ```bash
   just reset-for-local-development
   ```
   
   This creates an admin user with:
   - Username: `admin`
   - Password: `test`
   - Email: `admin@test.com`

4. Start the development server:
   ```bash
   just run
   ```

5. Visit http://localhost:8000 in your browser

### Common Commands

- `just run` - Run the development server
- `just migrate` - Run database migrations
- `just makemigrations` - Create new migrations
- `just reset-for-local-development` - Reset database with test data

For a full list of available commands, run:
```bash
just
```
