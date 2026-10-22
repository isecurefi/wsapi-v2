# WS-Channel API v2

WS-Channel specification version 2 (OpenAPI 2.0). Rewritten from v1
for clarity and modularity.

> **[API documentation is available online](https://www.isecure.fi/wsapi_v2/)**.

WS-Channel is SaaS for SEPA WebServices bank connections in
Finland.

Use the official [`isecure-ts-client`](https://github.com/isecurefi/isecure-ts-client)
for TypeScript, or [`wscli`](https://github.com/isecurefi/wscli-php) for the
command-line and PHP workflows.


The 2.17.0 specification adds optional account public-key armor for client-side inspection.
This additive field is qualified on gpgtest first; production promotion is separate.
Older deployments may omit `Accounts[].PgpKeys`. See the operation and schema descriptions
for unavailable entries and read-only handling.
