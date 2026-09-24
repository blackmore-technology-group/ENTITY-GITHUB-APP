# ENTITY GitHub App

Read-only GitHub integration for turning repository activity into normalized ENTITY evidence/provenance candidates.

This repository is intentionally separate from ENTITY Core. It is an adapter between GitHub and ENTITY; it does not redefine ENTITY identity, authority, rights, evidence, provenance, economic semantics, passports or verification rules.

## What it does

The app receives signed GitHub webhooks, verifies their integrity, minimizes the payload into a canonical evidence candidate, stores that candidate in a local SQLite evidence ledger and maintains a hash-chained audit trail.

Supported event families in v0.1:

- repository and installation lifecycle;
- pushes and Git refs;
- pull requests;
- check runs and check suites;
- Actions workflow runs;
- releases.

The API client can also authenticate as a GitHub App, exchange an installation token and obtain a read-only repository snapshot.

## What it does not do

A GitHub observation is evidence about GitHub state. It is not proof of legal ownership, objective truth, independent validation, regulatory approval, market adoption or accounting value.

It never treats a passing CI check as independent assurance and it does not mutate repositories in v0.1.

## Security model

The default permission set is read-only and follows least privilege. No GitHub App private key, webhook secret or installation token belongs in this repository. Secret/key file extensions and local databases are excluded by `.gitignore`.

Webhook requests require `X-Hub-Signature-256` verification before JSON is parsed. Repeated GitHub delivery IDs are deduplicated. Raw webhook bodies are not retained; the ledger stores a SHA-256 digest plus the minimized normalized candidate.

## Local requirements

- Windows 11 or another supported Python environment;
- Python 3.10+;
- OpenSSL for GitHub App RS256 signing.

BTG's local build uses Portable Git OpenSSL at:

`E:\ENTITY_ACTIVE\TOOLS\PortableGit\usr\bin\openssl.exe`

The path can be overridden with `ENTITY_GITHUB_OPENSSL`.

## Run tests

```powershell
$env:PYTHONPATH="$PWD\src"
python -m unittest discover -s tests -v
```

## Run the webhook receiver

```powershell
$env:PYTHONPATH="$PWD\src"
$env:ENTITY_GITHUB_WEBHOOK_SECRET="<set-outside-repository>"
python -m entity_github_app serve --host 127.0.0.1 --port 8787 --db .\state\entity-github-app.sqlite
```

Health endpoint: `GET /health`

Webhook endpoint: `POST /webhook`

Localhost is suitable for development only. GitHub requires a reachable HTTPS webhook endpoint for live delivery.

## GitHub App authentication

```powershell
python -m entity_github_app jwt --app-id <APP_ID> --private-key <PATH_TO_PRIVATE_KEY>
python -m entity_github_app snapshot --app-id <APP_ID> --private-key <PATH_TO_PRIVATE_KEY> --installation-id <ID> --repository owner/repo
```

The `jwt` command verifies that signing succeeds but deliberately does not print the JWT. The snapshot operation uses an installation access token in memory and performs only a read request.

## ENTITY boundary

The output contract is `entity.github.evidence-candidate.v1`. An ENTITY runtime may ingest or transform that candidate through its own governed adapter. The GitHub App is never the authority over ENTITY and does not embed changing v3.4 protocol internals.
