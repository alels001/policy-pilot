# PolicyPilot – Product Requirements (Pilot)

Setting: Nordwerk Automotive GmbH, a fictional automotive supplier used for this project.

## 1. Problem Statement
Employees regularly need information from internal HR, IT and Quality documents:
vacation and travel rules, IT how-tos, quality work instructions. These documents are
stored in different places and in several versions, so employees often ask colleagues
or open helpdesk tickets and get different answers. The pilot gives employees one
reliable entry point that answers only from approved, current documents, shows its
sources and respects access rights.

## 2. Pilot Users & Roles
Pilot group: about 15 users at one site. In the pilot, each user has exactly one role.

| Role | Typical questions | Can access |
|---|---|---|
| Employee | Vacation, travel expenses, IT access, code of conduct | General documents |
| HR Specialist | Same + salary bands, HR procedures | General + HR confidential |
| IT Admin | Same + incident runbooks, admin procedures | General + IT confidential |
| Quality Engineer | Same + internal audit reports | General + Quality confidential |

## 3. Top Questions
1. Wie viele Urlaubstage habe ich und wie beantrage ich Urlaub?
2. What can I claim for a two-day business trip?
3. Wie bekomme ich Zugriff auf ein neues Software-Tool?
4. What must I do if I receive a phishing email?
5. Welche Abweichungen wurden im letzten internen IATF-Audit festgestellt? (Quality Engineer only)
6. What is the salary band for a Senior Engineer? (HR Specialist only)

## 4. Scope
**In scope:**
- General documents: HR policies, travel and expense policy, code of conduct,
  IT FAQ and how-tos, quality handbook and work instructions
- Confidential documents per department: salary bands (HR), incident runbooks (IT),
  internal audit reports (Quality)
- German and English questions and documents
- Source references in every answer; "I don't know" when no evidence exists
- Role-based access control; thumbs up/down feedback

**Out of scope:**
- Personal employee data (individual salaries, sick days, performance reviews):
  never indexed
- Actions such as requesting vacation or resetting passwords (read-only assistant)
- Live systems (HR system, ticketing system)
- External or internet information

## 5. Data Sources
| Source | Example | Who can see it | Owner | Update frequency |
|---|---|---|---|---|
| HR policies | Urlaubsrichtlinie 2026 | All employees | HR | Yearly |
| Travel and expense policy | Reisekostenrichtlinie | All employees | HR / Finance | Yearly |
| Code of conduct | Verhaltenskodex | All employees | Compliance | On change |
| IT FAQ and how-tos | VPN setup guide | All employees | IT | On change |
| Quality handbook and work instructions | Incoming goods inspection | All employees | Quality | On change |
| Salary bands | Gehaltsbänder 2026 | HR Specialist only | HR | Yearly |
| Incident runbooks | Security incident response | IT Admin only | IT Security | On change |
| Internal audit reports | Internal IATF 16949 audit 2026 | Quality Engineer only | Quality | Per audit |

All documents in this project are synthetic.

## 6. Constraints
- Internal information only: the assistant must not answer from general model knowledge.
- Access rights are enforced during retrieval: a user never receives content from a
  document they are not allowed to open.
- Every answer references its sources (document, version, section).
- Only current, valid document versions are used.
- German and English.
- Data protection (GDPR): no personal employee data in the index; minimal personal
  data in prompts and logs.
- Read-only: the assistant does not change any system.

## 7. Success Metrics
Proposed targets for the pilot.

| Type | Metric | Target |
|---|---|---|
| Quality | Test questions answered correctly with the correct source | ≥ 85 % |
| Quality | Correct "I don't know" when the documents contain no answer | ≥ 90 % |
| Efficiency | Repetitive HR/IT helpdesk tickets during the pilot | −30 % |
| Adoption | Pilot users using the assistant weekly | ≥ 70 % |
| Safety | Answers containing content the user is not allowed to see | 0 |

## 8. Open Questions for a Real Rollout
- Where are the documents stored (SharePoint, intranet, network drives)?
- Can access groups be taken from the identity provider (e.g. Entra ID)?
- How should users with several roles be handled?
- Which LLM platforms and hosting regions are approved?
- Who owns each document and how often is it reviewed?
- Does logging user questions require Betriebsrat (works council) involvement?