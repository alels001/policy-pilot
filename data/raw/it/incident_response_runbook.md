# Security Incident Response Runbook – CONFIDENTIAL

Nordwerk Automotive GmbH · Version 2.2 · valid from 2026-04-01 · Owner: IT Security
Classification: Confidential – IT Admins only

## 1. Severity levels
| Level | Example | Response time |
|---|---|---|
| SEV1 | Ransomware on servers, production stopped | 15 minutes, 24/7 |
| SEV2 | Compromised user account with admin rights | 1 hour |
| SEV3 | Single infected laptop, phishing click without data loss | 4 hours (working hours) |

## 2. First steps for SEV1
2.1 Open a bridge call in Teams channel "#sec-incident" and page the on-call security engineer.
2.2 Isolate affected servers from the network via the EDR console ("Network containment").
2.3 Do **not** shut down affected machines, to preserve memory for forensics.
2.4 Inform the CISO and the plant managers of affected sites within 30 minutes.

## 3. Compromised account
3.1 Disable the account in the identity provider.
3.2 Revoke all active sessions and tokens.
3.3 Reset MFA methods and check mail forwarding rules created in the last 14 days.

## 4. Reporting obligations
If personal data may be affected, the data protection officer must be informed immediately. The legal deadline for reporting to the authority is 72 hours (Art. 33 GDPR).

## 5. Emergency contacts
On-call security engineer: internal number 4499, option 2. External incident response partner: contract number IR-2026-07 (details in the password vault, folder "IR").
