# Architecture

## Placement

`GitHub → ENTITY GitHub App → normalized evidence candidate → governed ENTITY ingestion adapter`

The app is outside ENTITY Core. GitHub remains the source system for the observed repository event. ENTITY remains responsible for interpreting any candidate according to the applicable ENTITY release and governance rules.

## Processing path

1. GitHub sends a webhook delivery.
2. The receiver checks body size and verifies `X-Hub-Signature-256` before parsing JSON.
3. The delivery is normalized into `entity.github.evidence-candidate.v1`.
4. The raw body is discarded; its SHA-256 is retained.
5. The candidate is deduplicated by GitHub delivery ID.
6. The candidate is stored in SQLite with its canonical SHA-256.
7. A hash-chained audit event records the local ingestion event.
8. A separately governed ENTITY adapter may consume the candidate.

## Stability boundary

The candidate schema contains GitHub observations, integrity metadata and explicit claim boundaries. It intentionally avoids embedding ENTITY v3.3 or v3.4 internal object layouts. That allows ENTITY to evolve while the GitHub connector remains a source adapter rather than a protocol fork.

## API authentication

GitHub App authentication uses RS256 JWTs signed by OpenSSL from a private key held outside the repository. Installation tokens are requested only when an API read is required and are not intentionally persisted.
