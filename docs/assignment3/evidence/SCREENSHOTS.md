# Screenshot evidence required

No screenshots captured. **Evidence not available.** Browser runtime connection timed out on initial connection and a troubleshooting attempt. Server-side template rendering passed but does not establish browser appearance. No real user database was opened for screenshots.

Use an isolated application/database with synthetic identities and health inputs. Capture with empty password fields and no tokens, credentials, real patient records or debug configuration. Show enough navigation/context to identify each screen.

| Caption | Exact screen / state |
| --- | --- |
| Figure 8a — Account registration | `/accounts/register/`, empty password, synthetic form data |
| Figure 8b — Login and pending approval | `/accounts/login/`, clean form and separate pending-approval error |
| Figure 9 — Patient dashboard/history | `/dashboard/`, synthetic user and synthetic saved reports |
| Figure 10a — Stroke indicators | `/predict/stroke/`, form with valid synthetic inputs |
| Figure 10b — Stroke result | Same route after submission; risk, percentage, advice, and any save warning |
| Figure 10c — Lung indicators/result | `/predict/lung-cancer/`, form and resulting synthetic score |
| Figure 12a — Pending appointment | `/dashboard/appointments/`, synthetic request/status |
| Figure 12b — Notifications | `/dashboard/notifications/`, synthetic notification and read control |
| Supplementary — Dataset missing state | `/dashboard/datasets/stroke-dataset/`, missing-file/credential message, no keys |

Verify desktop and mobile views, form errors, navigation and legibility. Record actual capture date, viewport, environment and synthetic fixture provenance. Replace placeholders in sections 4.1/5.3 only after capturing and reviewing the real UI.
