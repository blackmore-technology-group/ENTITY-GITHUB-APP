# Security Policy

## Reporting

Please report security issues privately to `blackmore.technology.group@gmail.com`. Do not publish exploit details, private keys, webhook secrets, installation tokens or sensitive repository content in a public issue.

## Credential rules

GitHub App private keys, webhook secrets and installation tokens must be stored outside the repository and outside generated evidence records. The application reads credentials only when required for authentication and does not intentionally persist tokens.

## Webhook trust boundary

A webhook is processed only after verification of `X-Hub-Signature-256` with the configured webhook secret. Successful signature verification establishes that the payload corresponds to the configured GitHub webhook secret; it does not establish objective truth, legal ownership or independent validation of claims contained in repository activity.

## Permissions

v0.1 is designed for read-only GitHub App permissions. Any future write capability requires a separate architecture/security review and an explicit release decision; write permission must not be added merely for convenience.

## Local evidence store

The SQLite ledger uses content hashes and a hash-chained audit record to detect accidental or subsequent inconsistency. It is not administrator-resistant WORM storage. Independent/off-device preservation is a separate deployment control.
