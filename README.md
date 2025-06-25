# Dashboard

A Flask web dashboard for managing vulnerability tests.

## Requirements

- Python 3.9+
- pip

## Installation

```bash
git clone https://github.com/FCeruzzi/dashboard.git
cd security_dashboard
py -3 -m venv .venv
.venv\scripts\activate
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
python.exe -m pip install --upgrade pip
pip install -r .\requirements.txt
```

## Environment Variables

The app relies on Flask's standard environment variables when using the `flask` command:

- `FLASK_APP` – module to run (set to `app.py`).
- `FLASK_ENV` – set to `development` to enable debug mode.
- `FLASK_RUN_PORT` – port used by `flask run` (optional).

A SQLite database in `instance/vulnerabilities.db` is created on first start and a default admin user `admin`/`admin` is added.

## Running the Application

### Using the Flask CLI

```bash
export FLASK_APP=app.py
flask run
```

### Directly with Python

```bash
python app.py
```

The application listens on port 5000 by default.

## Available Routes

| Method | Endpoint | Description | Authentication |
| ------ | -------- | ----------- | -------------- |
| GET/POST | `/login` | Login form | - |
| GET | `/logout` | Log out current user | login required |
| GET/POST | `/change_password` | Update current password | login required |
| GET/POST | `/add_user` | Create a user | admin only |
| GET/POST | `/users` | List existing users | admin only |
| GET | `/` | Redirects to `/home` | - |
| GET | `/home` | Landing page | - |
| GET | `/wapt_editor` | Vulnerability dashboard | login required |
| GET | `/sal` | SAL utility page | - |
| GET/POST | `/add` | Add vulnerability | admin or editor |
| GET/POST | `/edit/<id>` | Edit vulnerability | admin or editor |
| POST | `/delete/<id>` | Delete vulnerability | admin or editor |
| POST | `/duplicate/<id>` | Duplicate a record | login required |

## Authentication Flow

The application uses *Flask‑Login* for session management:

1. On startup the app ensures an administrator account exists.
2. Users authenticate via `/login` using their credentials.
3. After login users are redirected to `/wapt_editor`.
4. Routes are protected with `@login_required` and some require additional roles via the `role_required` decorator.
5. Sessions can be terminated with `/logout`.

To change the secret key or database path edit the corresponding values in `app.py`.
