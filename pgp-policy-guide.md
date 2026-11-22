## Availability and login

Use **isecure-ts-client 6.1.0 or newer**. The policy controls in this companion are deployed on:

| Environment | SDK BaseUrl |
| --- | --- |
| Test (gpgtest) | `https://ws-api.test.isecure.fi/v2` |
| Production release candidate (RC) | `https://ws-api.isecure.fi/rc` |

Key upload/list and account discovery also exist on production V2, with older policy metadata. Production `https://ws-api.isecure.fi/v2` retains its existing contract. It does not expose this policy administration API, and its legacy upload handler refuses policy-controlled uploads. Use the same RC endpoint for policy administration and the associated file uploads. Publishing SDK 6.1.0 does not promote RC to V2.

Register and complete Admin login/MFA using the [File Exchange authentication reference](https://www.isecure.fi/wsapi_v2/). The SDK defaults to the stronger password profile. Requests require both the account's API key and completed session's ID token. The SDK manages those headers. This reference does not send requests from your browser.

## Require your ERP plus a human approval

Register three eligible **authorize** public keys: ERP, person A and person B. Set `RequiredSignatureCount: 2` and `RequiredSignerFingerprints: [erpPrimaryFingerprint]`. Upload with detached signatures from ERP plus either person. Two people without ERP are refused; ERP alone is also insufficient.

A named signer counts toward N. Use full 40- or 64-character primary fingerprints; the server normalizes case. Signing subkeys count for their primary, and multiple signatures/subkeys from one primary count once. Registered keys must be usable and have at least 90 days of remaining validity when configuring or locking. Unknown, export-only, duplicate, expired or insufficient-lifetime keys are rejected.

~~~ts
// client: authenticated Admin WSChannel using the Test or RC BaseUrl above.
const result = await client.listAccounts();
const account = result.Accounts.find((item) => item.Email === accountEmail);
if (!account) throw new Error("Account not found");
const policy = account.PgpAuthorization;
if (policy?.State === "unavailable") throw new Error("Policy unavailable; stop");
await client.configureBankPgpPolicy("osuuspankki", {
  RequiredSignatureCount: 2,
  RequiredSignerFingerprints: [erpPrimaryFingerprint],
  ExpectedRevision: policy?.Revision ?? 0,
});
// Read the policy again after success before making another change.
~~~

The policy belongs to the signed-in account and bank, not every customer in the tenant. Other banks' settings are preserved. During bank migration, the server combines the applicable predecessor and target requirements. Existing file uploads still carry the original file and detached signatures. This authorization policy does not prevent duplicate payments at a bank.

## Editing, blocking and first-time setup

Read `Accounts[].PgpAuthorization` using `listAccounts()`. `RequiredSignatures` maps banks to N; `RequiredSignerFingerprints` maps banks to named primary fingerprints. An empty named-signer map means count-only checks. Missing metadata on an older deployment is not proof that it supports this feature; `State: unavailable` must never be shown as unlocked.

Use the exact `ExpectedRevision` from that read, or zero only when no policy exists. Refresh after a successful change, conflict or uncertain outcome. The SDK never automatically retries these mutations.

| Action | Method | Meaning |
| --- | --- | --- |
| Configure one bank | `configureBankPgpPolicy(bank, request)` | Set N and optionally named signers; preserve other banks |
| Omit `RequiredSignerFingerprints` | Same method | Preserve that bank's named signers |
| Send `RequiredSignerFingerprints: []` | Same method | Explicitly clear only the named-signer requirement; N still applies |
| Block one bank | `blockBankPgpPolicy(bank, { ExpectedRevision })` | Refuse uploads to that bank and remove its configured N/named signers |
| Re-enable a bank | `configureBankPgpPolicy(...)` | Make a new explicit choice of N and named signers |

N must be at least one; zero never disables PGP checks. Blocking every bank produces an explicit deny-all policy. Blocking does not retire a certificate or prevent downloads. Whole-policy `configurePgpPolicy` / `PUT /pgp/policy` has been removed; do not use it.

The first policy preserves one signature for other currently supported banks. Accounts with PGP exemptions or shared certificates must explicitly include `ConfirmPolicyInitialization: true` for that first change, acknowledging activation of checks for supported banks and linked callers. Do not add this automatically; it is rejected after initialization. Future banks remain blocked until explicitly enabled. No bank credentials or subscription access are granted by a policy change.

## Key deletion and irreversible locking

Use `deletePgpKey({ Fingerprint, ExpectedRevision })`, with a full primary fingerprint. The legacy short-ID `deleteKey()` endpoint is unsupported. A required primary cannot be deleted: first remove it from every applicable unlocked bank policy. Removing any key must also leave enough distinct eligible authorize keys for every allowed bank.

`lockPgpPolicy` permanently freezes **all account PGP keys and all bank policy settings**. There is no unlock, administrator override or operator bypass. It requires the reviewed revision and a fresh code from an already established SMS/TOTP factor, plus the opaque Admin action credential in `client.session.accessToken`. A fresh login alone is insufficient. For SMS, call `requestActionMfa(actionCredential)` before collecting the new code; for TOTP, collect a fresh authenticator code. Never log or persist the code, credential or request body.

Review all keys and bank settings before locking. Account audit history records these operations and survives account removal. Read it through the existing `listAuditEvents()` method; policy state itself is not audit history.
