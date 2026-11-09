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

## Password profile update (2.19.0)

The stronger `password-rsa-oaep-sha256-v1` profile is available on the existing v2 endpoints in production and test. There is no new API base URL. TypeScript SDK v5 defaults to it; installations pinned to v4 keep their legacy default. Python 1.0.0 and C# 1.0.0 also use the stronger profile by default. These SDKs offer an explicit legacy setting and never automatically downgrade after a failure.

New tenants must use the stronger profile for registration, login and password reset. Existing tenants explicitly enabled for legacy compatibility can use either profile, including when registering new customer accounts under their existing API key. Compatibility is a server-owned policy associated with the tenant/API key, not the SDK version or email address. Omitting the selector does not grant legacy access. Legacy mode cannot create a new tenant.

For TypeScript v5, omit `EncryptionProfile` to use the default. Set `EncryptionProfile: "legacy"` only for a compatible tenant. For Python 1.0.0 use `encryption_profile="legacy"`; for C# 1.0.0 use `PasswordProfiles.Legacy` in the client options. PHP 3.0.0's `Auth\PasswordProfile` helper defaults to the stronger profile; its existing CLI and raw generated client are separate legacy interfaces. See each SDK's release and migration guide before upgrading.

### Direct HTTP clients

1. Add `EncryptionProfile=password-rsa-oaep-sha256-v1` to the query of `InitRegister`, `InitLogin` or `InitPasswordReset`. For registration under an existing tenant, also pass the same `ApiKey` in initialization and registration; use `0` for a new tenant.
2. Require a successful response with the exact requested `EncryptionProfile`, `Challenge`, `KeyId` and `PublicKey`. An older server might ignore the query: missing or mismatched discovery must fail before password submission. Responses use `Cache-Control: no-store`; keep discovery only in memory for this attempt.
3. Encode the password as UTF-8 without normalization. Construct `0x01 || SHA256(exact ASCII Challenge) || uint16_be(UTF8(password).length) || UTF8(password)`. Encrypt this binary frame with the discovered RSA public key using OAEP SHA-256, MGF1-SHA-256 and an empty label; Base64-encode the ciphertext. The password limit is 283 UTF-8 bytes; the account's password-strength requirements still apply.
4. Submit `Encrypted`, the unchanged challenge as `ChResp`, and the exact `EncryptionProfile` and `KeyId`. Keep the email, mode, tenant and operation consistent. Never substitute a login challenge for a reset challenge or reuse discovery after changing identity/profile.

Discover the current key for each new attempt; do not pin a key or `KeyId` from documentation. Never log passwords, encrypted password bodies, challenges, reset codes or session credentials. Do not automatically retry password mutations or reset-code delivery, and do not retry a stronger-profile refusal as legacy.

Legacy-compatible tenants retain the existing `password||timestamp` encryption protocol when the wire selector is omitted. The SDK setting `"legacy"` is local configuration, not an `EncryptionProfile` value to send to the API. Extra JSON fields remain accepted for compatibility; they do not grant authority. Admin MFA, contact verification and account permissions are unchanged.

The authentication schemas are projected from the reviewed backend `config.json` and
`__wsapi.json.tmpl`; `password-profile.source.json` records their exact source. This
release updates six authentication operations only and does not promote the unrelated
account-lifecycle, provider or transfer contracts below.

## Credential-provider companion contract

[`provider-api.json`](provider-api.json) describes Maventa and MobilePay readiness and
connection administration on the test API and separately admitted production release
candidate, and Holvi connection administration on the test API. These operations are not yet
promoted to live production. Discovery in the main specification reports an enrollment, not
readiness or subscription authority.

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
deletion are unsupported for these providers. The SDK's `docs/providers.md` covers credential
bundles, MobilePay listing windows and complete JSON download envelopes.

Holvi (bank `holvi`, SFTP channel) adds Admin-only GET/PUT/DELETE
`/providers/holvi/connection` and GET `/providers/holvi/check`. PUT `{"SftpUser"}` with `If-Match: "absent"`
enrolls a server-generated Ed25519 key and returns only its public key, fingerprint and the
source addresses Holvi must allow; rotate by DELETE and PUT again. Check returns `00` with
`NewFiles` or `30` while Holvi has not registered the key. Holvi files use the main file
operations. The test API connects to the ISECure Bank Simulator, never to Holvi.

The online API-reference site is not changed merely by committing this companion.

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

## Encrypted file-transfer companion (unpublished)

[`transfer-api.json`](transfer-api.json) is generated from the backend's Test-only
transfer routes. It supplements the existing Files API; it does not add these
operations to current Production. The unpublished TypeScript SDK 4.6.0-rc.1 handles
negotiation, gzip, AES-256-GCM and presigned object transfers. Deployment is separate
from publication; always discover support in the authenticated session.

- **Existing integration:** continue calling `uploadFile` and `downloadFile` with
  ordinary Base64 Content. No new crypto or migration is required.
- **Compressed upload:** open an inline transfer with the original length/hash and
  `AcceptGzip: true`; create it, then execute with original bytes and their detached
  signatures. The SDK uses gzip only when negotiated and smaller.
- **Encrypted S3 upload:** open an S3 intent; create, prepare the original bytes,
  upload the prepared ciphertext, then explicitly execute. S3 gets ciphertext,
  never API authentication headers. Keys arrive only through the authenticated API.
- **Download:** create and execute a download intent, then receive the verified
  result. The SDK authenticates and checks integrity before releasing any bytes.
- **Timeout or expired URL:** keep the same ClientRequestId and transfer handle.
  Read status; do not automatically resubmit a bank operation. Refresh retained
  delivery to obtain a new URL without contacting the bank. Retirement denies new
  grants but cannot undo a bank operation or retract already delivered data.

The API ceiling is 32 MiB of original bytes. Local SDK/Rust/ordinary-HTTPS tests
passed both directions for compressible and incompressible files; upstream bank
and hosting limits still apply. The hosted Simulator's Lambda payload ceiling is
separate. No S3 protocol is imposed on banks. A leaked URL alone exposes encrypted
bytes, but possession of both a key and URL defeats that protection.

Temporary objects have one-day current and one-day noncurrent expiration, expired
marker cleanup and abandoned multipart cleanup. Periods run sequentially, round to
midnight UTC and delete asynchronously; permanent deletion within 24 hours is not
guaranteed. API grant/delivery expiry is enforced separately.

See the SDK's [file-transfer guide](https://github.com/isecurefi/isecure-ts-client/blob/main/docs/file-transfers.md)
for executable method examples. The companion source digest is retained in
`transfer-api.source.json`. Neither this commit nor local generation publishes it.

Bounded hosted Test checks passed with unpublished SDK 4.6.0-rc.1: inline upload,
encrypted S3 upload, download, retained encrypted delivery and retirement. These
small-file checks complement local 32-MiB interoperability; they do not claim
32-MiB capacity through the hosted Simulator Lambda. Production is unchanged.
