# GitHub App Registration

Register a GitHub App named **ENTITY GitHub App** owned by the BTG GitHub account/organization that will operate it.

## Required repository permissions for v0.1

- Metadata: Read (GitHub supplies this baseline permission)
- Contents: Read
- Pull requests: Read
- Checks: Read
- Actions: Read
- Commit statuses: Read

Optional only when the deployment will ingest those assurance signals:

- Security events: Read
- Vulnerability alerts: Read

Do not grant repository write, administration or organization permissions for v0.1.

## Webhook events

Subscribe to: `push`, `pull_request`, `check_run`, `check_suite`, `workflow_run`, `release`, `repository`, and `installation`.

Configure a cryptographically random webhook secret and store it outside the repository. Configure the live webhook URL only when a reachable HTTPS deployment exists. Local development can run with webhooks disabled or through an explicitly approved development tunnel.

## Credentials

After registration, record the App ID and create a private key. Store the private key outside Git, outside the repository directory and outside generated ENTITY evidence. Install the app only on repositories intentionally included in the evidence boundary.

## Production gate

Before enabling live webhooks, run the complete local test suite, verify permission scope, verify HTTPS endpoint ownership, perform a signed `ping`/test delivery, verify deduplication and audit integrity, and document key rotation/revocation custody.
