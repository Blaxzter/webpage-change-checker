# Full Stack FastAPI Template

> ## ⚠️ Status: Website-Monitoring hier ist unfertig und läuft nicht
>
> Dieses Repo war der erste Anlauf für einen Webseiten-Änderungs-Watcher, aufgesetzt
> auf dem FastAPI/Vue-Template. **Das Monitoring funktioniert nicht.** Die
> lauffähige Umsetzung lebt seit dem 02.08.2026 in einem eigenen Repo:
>
> ### → [github.com/Blaxzter/webwatcher](https://github.com/Blaxzter/webwatcher)
>
> Eigenständiges Python-Paket, Playwright + SQLite + Telegram, ohne Postgres und
> ohne Frontend. Läuft per Docker Compose oder systemd auf einem kleinen Server.
>
> ### Was hier konkret kaputt ist
>
> **1. Jede Prüfung stürzt sofort ab.** In `backend/app/logic/website_checker.py:101`
> (und an 12 weiteren Stellen):
>
> ```python
> start_time = datetime.now(datetime.timezone.utc)
> # AttributeError: type object 'datetime.datetime' has no attribute 'timezone'
> ```
>
> `datetime` ist hier die Klasse, nicht das Modul — richtig wäre
> `datetime.now(timezone.utc)`. Die Zeile steht *vor* dem `try`, der Aufrufer fängt
> alles ab und schreibt es als „failed check" in die Datenbank. Es kracht also nicht
> sichtbar, sondern scheitert still bei jeder Prüfung, für immer. Der Browser wird
> nie gestartet.
>
> **2. Sechs parallele Monitoring-Implementierungen** in `backend/app/logic/`
> (1642 Zeilen), keine davon getestet:
>
> | Datei | Zeilen | |
> | --- | --- | --- |
> | `website_checker.py` | 403 | wird über `threaded_monitor` gestartet, crasht |
> | `notification_service.py` | 347 | nur SMTP, kein Telegram |
> | `simple_website_checker.py` | 293 | Zweitfassung, gleicher Bug |
> | `adaptive_threaded_monitor.py` | 175 | |
> | `adaptive_monitoring_daemon.py` | 149 | |
> | `threaded_monitor.py` | 111 | |
> | `monitoring_daemon.py` | 88 | |
> | `background_service.py` | 76 | |
>
> Vier Daemon-Varianten und zwei Checker nebeneinander — typisches Muster für Code,
> der geschrieben, aber nie ausgeführt wurde. Ein `AttributeError` in Zeile 101 wäre
> beim ersten Start aufgefallen.
>
> **3. Benachrichtigung nur per SMTP.** Telegram, Screenshots im Diff und
> CSS-Klassen-Erkennung (nötig für Seiten, die ihren Zustand nur im
> `class`-Attribut kodieren) gibt es hier nicht.
>
> ### Was brauchbar ist
>
> Modelle (`app/models/website.py`), Schemas, CRUD und die Alembic-Migration sind
> ordentlich, ebenso die Vue-Views (`WebsiteDashboardView`, `WebsiteDetailView`,
> `components/website/`). Kaputt ist die Ausführungsschicht, nicht der Entwurf.
>
> ### Falls hier doch mal eine Weboberfläche entstehen soll
>
> Nicht den Code in `logic/` reanimieren, sondern `webwatcher` als Paket
> importieren: `browser.py`, `compare.py` und `store.py` dort sind bewusst frei von
> Framework-Abhängigkeiten. Die acht Dateien in `backend/app/logic/` können dann
> ersatzlos weg.



<a href="https://github.com/fastapi/full-stack-fastapi-template/actions?query=workflow%3ATest" target="_blank"><img src="https://github.com/fastapi/full-stack-fastapi-template/workflows/Test/badge.svg" alt="Test"></a>
<a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/fastapi/full-stack-fastapi-template" target="_blank"><img src="https://coverage-badge.samuelcolvin.workers.dev/fastapi/full-stack-fastapi-template.svg" alt="Coverage"></a>

## Technology Stack and Features

-   ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
    -   🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
    -   🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
    -   💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
-   🚀 [Vue 3](https://vuejs.org) for the frontend.
    -   💃 Using TypeScript, Composition API, Vite, and other parts of a modern frontend stack.
    -   🎨 [PrimeVue](https://primevue.org) for the frontend components with Aura theme.
    -   🔄 [@tanstack/vue-query](https://tanstack.com/query/latest) for server state management.
    -   📦 [Pinia](https://pinia.vuejs.org) for client state management.
    -   🎭 [Playwright](https://playwright.dev) for End-to-End testing.
    -   🦇 Dark mode support with PrimeVue theming.
    -   🤖 An automatically generated frontend client with type safety.
-   🐋 [Docker Compose](https://www.docker.com) for development and production.
-   🔒 Secure password hashing by default.
-   🔑 JWT (JSON Web Token) authentication.
-   📫 Email based password recovery.
-   ✅ Tests with [Pytest](https://pytest.org).
-   📞 [Traefik](https://traefik.io) as a reverse proxy / load balancer.
-   🚢 Deployment instructions using Docker Compose, including how to set up a frontend Traefik proxy to handle automatic HTTPS certificates.
-   🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.

### Home Screen

<img width="1135" height="782" alt="Home Screen" src="https://github.com/user-attachments/assets/d6e074e2-bb5c-40cf-9a46-f184fed45b35" />

### User Settings

<img width="1135" height="782" alt="User Settings" src="https://github.com/user-attachments/assets/212a7858-2c59-49a0-9c87-83431e5e9ba4" />

### Landing Page

<img width="1135" height="782" alt="Image" src="https://github.com/user-attachments/assets/40ab9187-84e3-44b8-a3fb-40aa66240209" />

### Dynamic Breadcrumbs

<img width="1135" height="782" alt="Image" src="https://github.com/user-attachments/assets/652b47f4-43bc-49ee-8c4c-ccde5f9bba7f" />

### Api Example view

<img width="1135" height="782" alt="Image" src="https://github.com/user-attachments/assets/79f4f91a-a5ff-43f5-947c-1bc7a7655959" />

## How To Use It

You can **just fork or clone** this repository and use it as is.

✨ It just works. ✨

### How to Use a Private Repository

If you want to have a private repository, GitHub won't allow you to simply fork it as it doesn't allow changing the visibility of forks.

But you can do the following:

-   Create a new GitHub repo, for example `my-full-stack`.
-   Clone this repository manually, set the name with the name of the project you want to use, for example `my-full-stack`:

```bash
git clone git@github.com:fastapi/full-stack-fastapi-template.git my-full-stack
```

-   Enter into the new directory:

```bash
cd my-full-stack
```

-   Set the new origin to your new repository, copy it from the GitHub interface, for example:

```bash
git remote set-url origin git@github.com:octocat/my-full-stack.git
```

-   Add this repo as another "remote" to allow you to get updates later:

```bash
git remote add upstream git@github.com:fastapi/full-stack-fastapi-template.git
```

-   Push the code to your new repository:

```bash
git push -u origin master
```

### Update From the Original Template

After cloning the repository, and after doing changes, you might want to get the latest changes from this original template.

-   Make sure you added the original repository as a remote, you can check it with:

```bash
git remote -v

origin    git@github.com:octocat/my-full-stack.git (fetch)
origin    git@github.com:octocat/my-full-stack.git (push)
upstream    git@github.com:fastapi/full-stack-fastapi-template.git (fetch)
upstream    git@github.com:fastapi/full-stack-fastapi-template.git (push)
```

-   Pull the latest changes without merging:

```bash
git pull --no-commit upstream master
```

This will download the latest changes from this template without committing them, that way you can check everything is right before committing.

-   If there are conflicts, solve them in your editor.

-   Once you are done, commit the changes:

```bash
git merge --continue
```

### Configure

You can then update configs in the `.env` files to customize your configurations.

Before deploying it, make sure you change at least the values for:

-   `SECRET_KEY`

You can (and should) pass these as environment variables from secrets.

Read the [deployment.md](./deployment.md) docs for more details.

### Generate Secret Keys

Some environment variables in the `.env` file have a default value of `changethis`.

You have to change them with a secret key, to generate secret keys you can run the following command:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the content and use that as password / secret key. And run that again to generate another secure key.

## How To Use It - Alternative With Copier

This repository also supports generating a new project using [Copier](https://copier.readthedocs.io).

It will copy all the files, ask you configuration questions, and update the `.env` files with your answers.

### Install Copier

You can install Copier with:

```bash
pip install copier
```

Or better, if you have [`pipx`](https://pipx.pypa.io/), you can run it with:

```bash
pipx install copier
```

**Note**: If you have `pipx`, installing copier is optional, you could run it directly.

### Generate a Project With Copier

Decide a name for your new project's directory, you will use it below. For example, `my-awesome-project`.

Go to the directory that will be the parent of your project, and run the command with your project's name:

```bash
copier copy https://github.com/fastapi/full-stack-fastapi-template my-awesome-project --trust
```

If you have `pipx` and you didn't install `copier`, you can run it directly:

```bash
pipx run copier copy https://github.com/fastapi/full-stack-fastapi-template my-awesome-project --trust
```

**Note** the `--trust` option is necessary to be able to execute a [post-creation script](https://github.com/fastapi/full-stack-fastapi-template/blob/master/.copier/update_dotenv.py) that updates your `.env` files.

### Input Variables

Copier will ask you for some data, you might want to have at hand before generating the project.

But don't worry, you can just update any of that in the `.env` files afterwards.

The input variables, with their default values (some auto generated) are:

-   `project_name`: (default: `"FastAPI Project"`) The name of the project, shown to API users (in .env).
-   `stack_name`: (default: `"fastapi-project"`) The name of the stack used for Docker Compose labels and project name (no spaces, no periods) (in .env).
-   `secret_key`: (default: `"changethis"`) The secret key for the project, used for security, stored in .env, you can generate one with the method above.
-   `smtp_host`: (default: "") The SMTP server host to send emails, you can set it later in .env.
-   `smtp_user`: (default: "") The SMTP server user to send emails, you can set it later in .env.
-   `smtp_password`: (default: "") The SMTP server password to send emails, you can set it later in .env.
-   `emails_from_email`: (default: `"info@example.com"`) The email account to send emails from, you can set it later in .env.
-   `postgres_password`: (default: `"changethis"`) The password for the PostgreSQL database, stored in .env, you can generate one with the method above.
-   `sentry_dsn`: (default: "") The DSN for Sentry, if you are using it, you can set it later in .env.

## Backend Development

Backend docs: [backend/README.md](./backend/README.md).

## Frontend Development

Frontend docs: [frontend/README.md](./frontend/README.md).

## Deployment

Deployment docs: [deployment.md](./deployment.md).

## Development

General development docs: [development.md](./development.md).

This includes using Docker Compose, custom local domains, `.env` configurations, etc.

## Release Notes

Check the file [release-notes.md](./release-notes.md).

## License

The Full Stack FastAPI Template is licensed under the terms of the MIT license.
