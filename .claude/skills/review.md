---
name: review
description: >
  Run the full code review pipeline: dep-checker (versions + CVEs) + logic-reviewer
  (DB, security, logic bugs) orchestrated by code-reviewer. If the two reviewers
  conflict, arbitrator steps in to find the best compromise for the project.
  Use when asked to review, audit, or check the codebase before a merge.
---

Invoke the `code-reviewer` agent with this prompt:

```
Run the full review pipeline for the animal project:

1. Spawn dep-checker and logic-reviewer IN PARALLEL.

2. dep-checker: read pyproject.toml, check all [tool.poetry.dependencies] against
   PyPI latest versions and the OSV CVE database. Return the Dependency Report table
   and Summary bullets.

3. logic-reviewer: review app/db/mixins.py, app/db/models/animal.py,
   app/repo/base_repository.py, app/services/animal_service.py,
   app/routers/animal_router.py for N+1 queries, wrong column types, missing
   transaction scope, unvalidated getattr, missing auth, and logic bugs.
   Return findings per category plus a Verdict.

4. Check for conflicts between the two reports (upgrade vs. API breakage, CVE
   reachability disagreement, mutually exclusive fixes, PASS vs. FAIL on same issue).

5. If conflicts exist: invoke the arbitrator agent with both full reports.
   The arbitrator's Arbitrated Action Plan overrides both sub-agents on disputed points.

6. Produce a final merged report with sections:
   - Dependency & Security Advisories
   - Logic, DB & Security Findings
   - Conflict Resolution & Action Plan (arbitrator output or "no conflicts")
   - Overall Verdict + must-fix list ordered by severity
```
