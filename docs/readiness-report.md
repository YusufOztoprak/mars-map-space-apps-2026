# Readiness report

## Chrome update — 15 November 2026

[Actual Chrome smoke test](chrome-smoke-2026-11-15.md): 3D loading, three candidate routes, Balanced selection, slope toggle/legend, Clear, invalid input and same-point recovery passed. Some remote tiles failed with an explicit fallback warning. **Legacy 2D startup FAILED on this Windows checkout**: CRLF conversion changes the Leaflet JS bytes, causing SRI rejection and `L is not defined`. This supersedes the generic browser-pending status below for the executed smoke scenarios; 2D retesting and unexecuted scenarios remain pending. Product files were not changed.

Updated 15 November 2026. Product source baseline: main `008cf734fab40d5cad606170b37f6435d60775be`, with integration-only changes on `entegrasyon-test`. No backend/frontend product files were modified.

## Decision

Automated integration acceptance passes: **103 Python tests, 12 current 2D flow tests, 6 Explorer policy tests; no failures**. Final device/demo acceptance remains pending.

## Completed integration work

- Synchronized the integration branch with current main while preserving local work.
- Removed historical commit pins from backend/frontend test inputs.
- Replaced obsolete SKIP placeholders with actual error, real-route and projection checks.
- Updated current English test documentation and retained reproducible outputs.
- Kept real CTX/MOLA products ignored and left team product code unchanged.

## Outstanding human/device gates

| Gate | Owner | Status |
| --- | --- | --- |
| Actual demo computer setup | Demo operator + integration/test | Pending; rehearsal machine is different |
| Chrome 3D rendering and interactions | Integration/test + demo operator | Pending visual walkthrough |
| Chrome legacy 2D draw/reset/popups | Integration/test | Pending real browser walkthrough |
| Physical phone selection/orientation/layers | Phone operator + integration/test | Pending device access |
| All remote imagery under demo network conditions | Demo operator + frontend/data owners | Pending live visual check |

The app now serves frontend/API together on port 5000. Follow the current README; the former separate-port setup is optional. Phone localhost refers to the phone, not the PC: owners must agree on a reachable serving strategy without silently changing security/network configuration.

## Delivery

See [test-report.md](test-report.md) for exact results and data requirements and [e2e-plan.md](e2e-plan.md) for the operator runbook. Test/fixture improvements do not constitute astronaut safety certification, full scientific validation, or a claim that browser checks have passed. The 20-degree exclusion remains a prototype parameter.
