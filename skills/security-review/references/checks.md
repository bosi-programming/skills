# Security checks

What the reviewer checks a diff against. Each row has the id, what a diff shows
when the check fails, and a default severity. Severities are `critical`,
`high`, `medium` and `low`; move one up or down by what the code does, and say
why in the finding. Only what a diff can show is listed.

## OWASP Top 10 (2021)

| Id | What the diff shows | Severity |
| --- | --- | --- |
| A01:2021 | Broken access control: a route or handler with no permission check, an id taken from the request without an ownership check, CORS open to every origin with credentials, a check done only on the client | high |
| A02:2021 | Cryptographic failures: MD5 or SHA-1 for passwords, ECB mode, a fixed IV or salt, a key of fewer than 128 bits, TLS verification off, sensitive data sent or stored in clear text | high |
| A03:2021 | Injection: SQL, shell, LDAP, template or NoSQL text built by concatenating outside input, `eval` or `exec` on outside input, HTML written without escaping | critical |
| A04:2021 | Insecure design: no rate limit or lockout on a login or reset route, a trust boundary the diff removes, a business limit enforced only on the client | medium |
| A05:2021 | Security misconfiguration: debug mode on, default credentials, directory listing, verbose errors that return stack traces, a security header removed, XML external entities enabled | medium |
| A06:2021 | Vulnerable and outdated components: a dependency added or bumped to a version with a known advisory, an unpinned dependency, a package from an unofficial source | medium |
| A07:2021 | Identification and authentication failures: a hard-coded secret, key or password, a weak password rule, a session id in a URL, a session not renewed at login, a token with no expiry | high |
| A08:2021 | Software and data integrity failures: deserialising outside data with `pickle`, `yaml.load` or similar, a download run without a checksum or signature, a CI step that runs unreviewed code | high |
| A09:2021 | Security logging and monitoring failures: a password, token or card number written to a log, a failed login or access denial not logged, a log entry built from unescaped outside input | low |
| A10:2021 | Server-side request forgery: a server request to a URL taken from outside input with no allow-list, a redirect target taken from the request | high |

## OWASP ASVS 4.0.3 level 1

| Id | What the diff shows | Severity |
| --- | --- | --- |
| V2.1.1 | A password rule shorter than 12 characters | low |
| V2.1.7 | A new password not checked against a list of breached passwords | low |
| V2.4.1 | Passwords stored with a fast hash or in clear text instead of a salted, slow hash | high |
| V2.10.4 | A secret, key, password or token written in source, config or a build file, not read from a vault or the environment | high |
| V3.2.1 | A new session not created at login, so an old session id stays valid | medium |
| V3.4.1 | A session cookie set without `Secure` | medium |
| V3.4.2 | A session cookie set without `HttpOnly` | medium |
| V3.5.2 | A session token that is a static API secret instead of a revocable token | medium |
| V4.1.1 | An access control rule enforced only on the client, not on a trusted server layer | high |
| V4.1.3 | A function reachable without the least privilege it needs | medium |
| V4.2.1 | A record read or changed by an id from the request with no ownership check | high |
| V5.1.3 | Outside input accepted with no allow-list or format validation | medium |
| V5.2.1 | Outside HTML rendered with no sanitiser | high |
| V5.3.4 | A database query built by concatenation instead of a parameterised query | critical |
| V5.3.8 | An operating-system command built from outside input | critical |
| V6.2.1 | A cipher or mode not on an approved list, or a hash that is broken | high |
| V6.2.2 | A random value for a token, id or nonce taken from a source that is not cryptographically secure | high |
| V7.1.1 | A credential or session token written to a log | medium |
| V8.3.4 | Sensitive data returned in a response, a URL or a cache that does not need it | medium |
| V9.1.1 | A connection to a remote service in clear text instead of TLS | high |
| V10.2.1 | Code that sends data to an unexpected host or runs a hidden backdoor | critical |
| V12.3.1 | A file path built from outside input with no check against path traversal | high |
| V12.5.1 | An upload served back with no content-type or extension check | medium |
| V13.2.1 | A REST method not limited to the methods the route needs | low |
| V14.2.1 | A dependency pinned to a version with a known advisory | medium |
| V14.4.3 | A response that lacks a content security policy where the diff adds HTML output | low |
