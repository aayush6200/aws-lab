# 07 — Full trace: one line of Python → AWS endpoint → back

The call being traced, end to end:

```python
from common.factory import get_client      # (the factory being designed)
s3 = get_client("s3", profile="aayush_dev")
resp = s3.list_buckets()
```

Everything below happens for THIS one call. Steps marked **[LOCAL]** never
touch the network. Steps marked **[NETWORK]** leave the machine. Steps marked
**[AWS]** happen inside Amazon's datacenter, where my code has no vote.

---

## PHASE 0 — before any of this: what's already sitting on disk

| file | what it is | lifetime | created by |
|---|---|---|---|
| `~/.aws/config` | profiles + sso-session (recipes, no secrets) | permanent | me, by hand |
| `~/.aws/sso/cache/<hash>.json` (registration) | the CLI registered itself as an OIDC app with Identity Center | ~90 days | first-ever `aws sso login` |
| `~/.aws/sso/cache/<hash>.json` (token) | **the PROOF** — "this is aayush_dev", no account, no role | ~8 hrs | `aws sso login` |
| `~/.aws/cli/cache/<hash>.json` | **the PERMIT** — temp AccessKeyId/Secret/SessionToken for ONE account+role | ~1 hr | minted on first API call |

Mental model: proof = hotel keycard (who I am). Permit = room key cut from it
(what I may act as, where). Config = the reservation. Registration = the
hotel's app installed once on my phone.

---

## PHASE 1 — `boto3.Session(profile_name="aayush_dev")`  [LOCAL]

1. botocore reads `~/.aws/config`, finds `[profile aayush_dev]`.
2. Sees `sso_session = aws-lab` → follows it to the `[sso-session aws-lab]`
   block → start URL + SSO region.
3. Records: region `us-east-1`, account `685108782540`, role `DevAccess`.
4. **Nothing else happens.** No network. No credential is read yet. A Session
   is a wallet, not a connection — it's config held in a Python object.

> Misconception killed here: there is no "session with AWS" to keep alive.
> Nothing is connected. Expiry is a property of the token files, not of this
> object.

## PHASE 2 — `session.client("s3")`  [LOCAL]

1. botocore loads the **service model** for S3 from its bundled JSON
   (`botocore/data/s3/...`): every operation, parameter, error shape.
   This is how boto3 "knows" `list_buckets` exists — it's data, not code.
2. **Endpoint resolution**: service `s3` + region `us-east-1` →
   `https://s3.us-east-1.amazonaws.com`. Just string construction from a
   bundled endpoints table. Still no network.
3. Credentials are wired up **lazily** — a resolver is attached, not executed.
   A client with a dead token is created successfully; it only blows up when
   used. (This is why the factory can't validate credentials at build time
   without making a real call.)

## PHASE 3 — `s3.list_buckets()` — credential resolution  [LOCAL → maybe NETWORK]

Now, and only now, boto3 needs actual keys to sign with. The SSO credential
provider runs this chain:

```
need permit (cli/cache) ──► exists? not expired? ──yes──► use it      [LOCAL]
        │ no / expired
        ▼
need proof (sso/cache token) ──► exists? not expired? ──no──► FAIL:
        │ yes                      UnauthorizedSSOTokenError /
        ▼                          "Token has expired... run aws sso login"
[NETWORK] call SSO: GetRoleCredentials(accountId=6851..., roleName=DevAccess,
                                        accessToken=<proof>)
        ▼
fresh permit (≈1 hr) returned ──► written to ~/.aws/cli/cache ──► use it
```

Decisions this encodes:
- A valid permit means **zero** auth traffic — straight to Phase 4.
- A dead permit + live proof = silently re-minted. I feel nothing.
- A dead proof = unfixable by code. Only a human in a browser
  (`aws sso login`) can make a new one. **The factory's job here is purely
  translation**: catch this error and print "run `aws sso login`" instead of
  an eight-frame stack trace. It cannot refresh anything itself.

## PHASE 4 — building & signing the request  [LOCAL]

1. Service model + my arguments → an HTTP request:
   ```
   GET /  HTTP/1.1
   Host: s3.us-east-1.amazonaws.com
   x-amz-date: 20261016T071500Z
   x-amz-security-token: <SessionToken from the permit>
   ```
2. **SigV4 signing**: botocore canonicalizes the request (method, path,
   sorted headers, payload hash) and computes an HMAC chain using the
   permit's SecretAccessKey, scoped to date/region/service:
   ```
   Authorization: AWS4-HMAC-SHA256
     Credential=ASIA.../20261016/us-east-1/s3/aws4_request,
     SignedHeaders=host;x-amz-date;...,
     Signature=<hex>
   ```
   Three identity facts ride on EVERY request:
   - `Credential=ASIA...` → which permit (temporary keys start with ASIA,
     long-lived IAM keys with AKIA — you can spot the difference in logs)
   - `x-amz-security-token` → the session token proving the keys are STS-minted
   - the signature itself → proves possession of the secret **without sending it**

   > This is why "how do we know if it's dev or admin calling?" has a
   > structural answer: identity is not a parameter anyone passes honestly —
   > it is cryptographically welded to the request. There is no anonymous call.

## PHASE 5 — the wire  [NETWORK]

1. DNS: `s3.us-east-1.amazonaws.com` → AWS front-end IPs.
2. TCP handshake, then TLS — server presents an Amazon cert; everything
   after is encrypted.
3. The signed HTTPS request is sent. One request. No persistent tunnel;
   boto3 keeps the TCP connection pooled for reuse, but that's a transport
   optimization, not a "session" in any auth sense.

## PHASE 6 — inside AWS  [AWS] — where EVERY security decision actually happens

1. **AuthN — who is this?** The front end recomputes the signature from the
   request + its copy of the secret for `ASIA...`. Match → request genuinely
   came from the holder of that permit, untampered. The permit maps to:
   ```
   arn:aws:sts::685108782540:assumed-role/AWSReservedSSO_DevAccess_35d11f1c1e9d8a18/aayush_dev
   └── the role being worn ──────────────────────────────┘ └── who wears it ──┘
   ```
   Expired permit → rejected here (`ExpiredToken`), before any policy is read.
2. **AuthZ — may this identity do `s3:ListAllMyBuckets`?** IAM evaluates the
   policies attached to the DevAccess permission set's role (plus any SCPs the
   org sets above the account). Explicit deny > allow > default-deny.
   - Allowed → S3 service executes the operation.
   - Not allowed → `403 AccessDenied`, and **this** is the place my earlier
     "block it in the factory" idea actually lives. Client-side checks would
     be decoration: bypassable (anyone can call boto3 directly) and a second
     rulebook that drifts from the real one. Enforcement lives where it
     cannot be stepped around.
3. **Audit**: the call lands in CloudTrail with the full assumed-role ARN —
   dev and admin remain distinguishable forever, per request. (And if a
   teammate also wore DevAccess, the `/aayush_dev` suffix still tells us apart.)

## PHASE 7 — the way back  [NETWORK → LOCAL]

- `200` + XML body → botocore parses it against the service model →
  `{"Buckets": [...], "Owner": {...}}` — a plain dict in my hands.
- `403 AccessDenied` → botocore raises `ClientError` with
  `resp["Error"]["Code"] == "AccessDenied"`. The factory (or a wrapper) can
  catch this and say: *"Running as dev; this action isn't in DevAccess. If
  legitimate, rerun with profile=aayush_admin"* — translate, never auto-retry
  as admin (auto-escalation would make least-privilege a polite fiction:
  every denied call would silently become an admin call).

---

## The whole thing on one screen

```
my code
  └─ get_client("s3", profile="aayush_dev")
       └─ Session: read ~/.aws/config ................. [LOCAL]  wallet, no network
       └─ client: service model + endpoint string ..... [LOCAL]  lazy creds
  └─ s3.list_buckets()
       └─ permit valid? ──no──► proof valid? ──no──► ERROR: aws sso login (human)
       │                          └──yes──► GetRoleCredentials ► new permit  [NETWORK]
       └─ build HTTP request + SigV4 sign (identity welded on) [LOCAL]
       └─ DNS → TCP → TLS → send ...................... [NETWORK]
       └─ AWS: verify signature (WHO) ► IAM policy eval (ALLOWED?) ► run or 403  [AWS]
       └─ parse response → dict, or ClientError → factory translates  [LOCAL]
```

## What this trace settles for the factory design

| axis | what the trace shows |
|---|---|
| caching | Session = cheap local object; cache one per profile. Clients = cheaper; rebuild or cache, low stakes. Nothing network-y is being "kept alive". |
| privilege | chosen ONCE, at session build, via profile. After that it's welded to every request. Factory's only privilege decision: which profile default (dev). |
| failure UX | two distinct failures to translate: dead proof (→ "run aws sso login") and AccessDenied (→ "needs admin, rerun explicitly"). Both arrive as exceptions in Phase 3/7. |
| config | profile names/region are client-side strings read in Phase 1 — fine to centralize in the factory. Account IDs/policies are server-side — factory never needs them. |
| enforcement | ALL of it is Phase 6, inside AWS. The factory owns construction + translation, zero authorization. |
| auto-retry as admin | never — it converts every denial into silent escalation; CloudTrail would show admin doing dev's work and least-privilege dies quietly. |

---

## APPENDIX — a REAL denial, captured live (2026-10-16)

Deliberately called a service DevAccess doesn't cover, as `aayush_dev`:

```python
session = boto3.Session(profile_name="aayush_dev")
client  = session.client("iam")
client.list_users()        # → ClientError
```

**Where it started / where it was sent** (both knowable BEFORE the call, from
the client object — this is what the factory should log on every build):

```
service : iam                              client.meta.service_model.service_name
endpoint: https://iam.amazonaws.com        client.meta.endpoint_url
region  : aws-global                       client.meta.region_name
```

(IAM is a GLOBAL service — no region in its endpoint, unlike
`s3.us-east-1.amazonaws.com`. The endpoint table in Phase 2 decided this.)

**The error exactly as AWS returned it** (`e.response` on the ClientError):

```json
{
  "Error": {
    "Type": "Sender",
    "Code": "AccessDenied",
    "Message": "User: arn:aws:sts::685108782540:assumed-role/AWSReservedSSO_DevAccess_35d11f1c1e9d8a18/aayush_dev is not authorized to perform: iam:ListUsers on resource: arn:aws:iam::685108782540:user/ because no identity-based policy allows the iam:ListUsers action"
  },
  "ResponseMetadata": {
    "RequestId": "ff098bc6-274e-47cd-81fa-a8430cc1eb29",
    "HTTPStatusCode": 403,
    "RetryAttempts": 0
  }
}
```

Reading it — AWS's one sentence contains the entire Phase 6 story:

| fragment | meaning |
|---|---|
| `Type: "Sender"` | the fault is the caller's (4xx), not AWS's (that would be `Receiver`/5xx) |
| `Code: "AccessDenied"` | AuthN PASSED (signature was valid — AWS knows exactly who I am); AuthZ FAILED |
| `User: arn:...DevAccess.../aayush_dev` | the welded-on identity from the SigV4 signature — proof there are no anonymous calls |
| `not authorized to perform: iam:ListUsers` | the exact action string IAM evaluated |
| `because no identity-based policy allows...` | the REASON class: default-deny (nothing allowed it) — different from an explicit Deny, which would say so |
| `RequestId` | the correlation key — this exact ID appears in CloudTrail; log it ALWAYS |
| `HTTPStatusCode: 403` | plain HTTPS underneath it all |
| `RetryAttempts: 0` | botocore knows a 403 is deterministic — retrying won't change a policy |

**What the factory should log per request, from this**:
`service, endpoint, operation, Error.Code, RequestId` — enough to replay the
whole story later, and the RequestId ties the client-side log line to the
server-side CloudTrail record of the same event.
