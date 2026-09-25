# ENTITY GitHub App

**Read-only GitHub integration for turning repository activity into normalized ENTITY evidence/provenance candidates.**

[ENTITY v3.4.0](https://github.com/blackmore-technology-group/ENTITY/releases/tag/v3.4.0) · [Developer portal](https://github.com/blackmore-technology-group/ENTITY/blob/main/DEVELOPERS.md) · [Engineering evidence](https://github.com/blackmore-technology-group/ENTITY/blob/main/docs/ENGINEERING_EVIDENCE.md) · [Security](https://github.com/blackmore-technology-group/ENTITY/blob/main/SECURITY.md)

This repository is intentionally separate from ENTITY Core. It is an adapter between GitHub and ENTITY; it does **not** redefine ENTITY identity, authority, rights, evidence, provenance, economic semantics, Global Passports or verification rules.

## Why this exists

GitHub already produces useful signed/attributed operational events: pushes, refs, pull requests, checks, workflow runs and releases. The ENTITY GitHub App converts a bounded subset of those observations into a minimized evidence-candidate format that an ENTITY runtime can ingest through its own governed adapter.

That makes the app useful for developers evaluating questions such as:

- Can repository activity become portable provenance without making GitHub the authority over ENTITY?
- Can CI/release observations be retained as evidence while keeping “passing check” separate from “independent validation”?
- Can a provider-specific webhook be normalized into a provider-independent evidence candidate?
- Can repository evidence be hash-chained and audited without retaining raw webhook payloads?

## What it does

The app:

1. receives signed GitHub webhooks;
2. verifies `X-Hub-Signature-256` before parsing JSON;
3. minimizes supported payloads into canonical evidence candidates;
4. stores candidates in a local SQLite evidence ledger;
5. maintains a hash-chained audit trail;
6. can authenticate as a GitHub App and obtain a read-only repository snapshot.

Supported event families in v0.1:

- repository and installation lifecycle;
- pushes and Git refs;
- pull requests;
- check runs and check suites;
- Actions workflow runs;
- releases.

## What it does not do

A GitHub observation is evidence about GitHub state. It is **not** proof of legal ownership, objective truth, independent validation, regulatory approval, market adoption or accounting value.

The app never treats a passing CI check as independent assurance and does not mutate repositories in v0.1.

It is also not the authority over ENTITY. The output contract is `entity.github.evidence-candidate.v1`; an ENTITY runtime decides whether and how that candidate participates in a governed state transition.

## Quick start

Requirements:

- Python 3.10+;
- OpenSSL with RSA signing support for GitHub App authentication;
- a local test environment or a reachable HTTPS endpoint for live GitHub webhooks.

Optional editable install from the repository root:

```bash
python -m pip install -e .
```

The project currently declares no third-party runtime dependencies, so you can also run the tests directly from `src` without installing the package.

PowerShell:

```powershell
$env:PYTHONPATH="$PWD\src"
python -m unittest discover -s tests -v
```

Bash/zsh:

```bash
export PYTHONPATH="$PWD/src"
python -m unittest discover -s tests -v
```

No BTG-specific filesystem path is required. If your OpenSSL executable is not discoverable normally, set `ENTITY_GITHUB_OPENSSL` to the executable path in your own environment.

## Run the webhook receiver

PowerShell:

```powershell
$env:PYTHONPATH="$PWD\src"
$env:ENTITY_GITHUB_WEBHOOK_SECRET="<set-outside-repository>"
python -m entity_github_app serve --host 127.0.0.1 --port 8787 --db .\state\entity-github-app.sqlite
```

Bash/zsh:

```bash
export PYTHONPATH="$PWD/src"
export ENTITY_GITHUB_WEBHOOK_SECRET="<set-outside-repository>"
python -m entity_github_app serve --host 127.0.0.1 --port 8787 --db ./state/entity-github-app.sqlite
```

Endpoints:

- health: `GET /health`
- webhook: `POST /webhook`

`127.0.0.1` is suitable for local development only. GitHub requires a reachable HTTPS webhook URL for live delivery.

## GitHub App authentication

```bash
python -m entity_github_app jwt --app-id <APP_ID> --private-key <PATH_TO_PRIVATE_KEY>
python -m entity_github_app snapshot --app-id <APP_ID> --private-key <PATH_TO_PRIVATE_KEY> --installation-id <ID> --repository owner/repo
```

The `jwt` command verifies that signing succeeds but deliberately does not print the JWT. The snapshot operation uses an installation access token in memory and performs only read operations.

## Security model

The default permission set is read-only and follows least privilege.

Never commit:

- GitHub App private keys;
- webhook secrets;
- installation tokens;
- production SQLite ledgers;
- credentials or operational ENTITY authority material.

Secret/key file extensions and local databases are excluded by `.gitignore`. Repeated GitHub delivery IDs are deduplicated. Raw webhook bodies are not retained; the ledger stores a SHA-256 digest plus the minimized normalized candidate.

## ENTITY v3.4 boundary

ENTITY v3.4.0 adds the Global Passport and continuous-provenance surfaces, but this adapter intentionally does not embed changing v3.4 protocol internals. Its responsibility is narrower: produce an attributed evidence candidate that ENTITY Core may ingest under its own authority, rights, evidence and verification rules.

That separation is deliberate. GitHub can be an evidence source without becoming a sovereign authority.

## Contributing

Useful contributions include:

- webhook fixture coverage for supported public event families;
- cross-platform setup corrections;
- payload minimization/privacy review;
- replay/deduplication tests;
- audit-chain verification tests;
- documentation improvements that make the GitHub→ENTITY evidence boundary clearer.

For protocol-level contribution, Global Passport work, domain packages or independent conformance, start in the main [ENTITY repository](https://github.com/blackmore-technology-group/ENTITY).
