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
This additive field is available in production and the test API. Credential-provider discovery
reports enrollment only; it does not establish provider-operation availability.
Older deployments may omit `Accounts[].PgpKeys`. See the operation and schema descriptions
for unavailable entries and read-only handling.

## Credential-provider companion contract

[`provider-api.json`](provider-api.json) describes Maventa and MobilePay readiness and
connection administration on the test API and separately admitted production release
candidate. These operations are not yet promoted to live production. Discovery in the
main specification reports an enrollment, not readiness or subscription authority.

The companion adds GET `/providers/{provider}/check` and GET/PUT/DELETE
`/providers/{provider}/connection`, with concrete `maventa` and `mobilepay` paths.
Readiness returns Ready and Environment. Admin metadata returns Enrolled, Environment
and Version, never credential values. PUT/DELETE require If-Match and Idempotency-Key;
retain exact input/version/key after an uncertain outcome. The server enforces the
signed-in account, tenant, role, provider subscription and deployment environment.
Maventa accepts Stage credentials on test and production credentials on production RC;
MobilePay uses production reporting credentials only when explicitly enrolled.

File listing, downloads and compatible enrollment reuse the main API operations.
Maventa/MobilePay connections have `Certificates: []` and must still appear in clients.
Supported types are `MAVENTA_INVOICE_JSON_V1`, `MOBILEPAY_FUNDS_JSON_V1` and
`MOBILEPAY_FEES_JSON_V1`. Omitted Status, ALL and DLD are equivalent; NEW is unsupported.
DLD is a descriptor convention, not server-maintained download history. Upload and file
deletion are unsupported for these providers. The candidate SDK's `docs/providers.md` covers credential bundles, MobilePay listing
windows and complete JSON download envelopes.
The SDK candidate remains unpublished during qualification; the online API-reference
site is not changed merely by committing this companion.

The backend's `config.json` and `__wsapi.json.tmpl` remain authoritative.
`scripts/export-provider-contract.py` in that repository generates the companion and
checks deterministic drift with `--check`. `provider-api.source.json` records its owning
path and SHA-256, identical to the SDK's vendored companion. Update these files only
from the reviewed backend export. The main production specification is unchanged.


## Unreleased account lifecycle update (2.18.0)

`DeleteAccount` revokes both sign-ins and retains the customer record with `Lifecycle: deleted`,
`DeletedAt`, `DeletedBy` and `PurgeAfter`. Deleted customers contribute no customer licenses.
Automatic removal becomes eligible after 30 days; physical removal is asynchronous. Audit
history remains available independently. Integrator-owner accounts remain protected.

Account deletion and certificate retirement each require a fresh Admin MFA login, no more than
ten minutes old and usable for one lifecycle action. These changes are not yet deployed.

The deletion request now requires `ConfirmSoftDelete` equal to the target email and must omit
the legacy `Confirm` field. This fails safely against a backend that still implements immediate
deletion. Update clients together with the backend; older deletion requests are rejected.

Account discovery includes optional `Accounts[].CreatedAt`, the original account registration
instant in UTC RFC3339 format. Adding another sign-in mode does not change it. Legacy accounts
without a recorded timestamp omit this field; clients should show an unknown registration date.
