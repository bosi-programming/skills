# Observability

An NFR without a way to watch it in production is a wish. Each NFR whose
measure can be read at runtime ships with its observability plan: logs,
metrics, a dashboard widget and a monitor, in the monitoring tool the
project already uses, such as Datadog or Sentry. Ask the engineer which
one when the codebase does not make it clear.

## When it applies

- **Applies** — anything measured while the system runs: latency, error
  rate, uptime, throughput, queue depth, retries, failed logins, drop-off
  on a screen.
- **Does not apply** — anything measured once, outside production:
  install steps, code modularity, a yearly audit. Write
  `Observability: N/A — verified by <test, review or audit>` and say why.

## Reuse before you add

Before you propose anything new, search the codebase and the monitoring
tool for what already exists:

- Logs: `logger.info|warn|error` calls and logger tag constants in the
  touched modules.
- Traces: tracing spans in the touched modules. Tracing already gives
  latency and error rate per span and per endpoint.
- Real user monitoring: for screen-level NFRs, check what the tool
  records for the screens the project touches.
- Existing dashboards, monitors and alerts: use the MCP server or CLI the
  session has for the tool.

Cite what you found. Mark anything new as `proposed`.

## What to specify per NFR

| Item | What to write |
|---|---|
| Logs | Event, level, structured fields and logger tag. No PII in any field. Use the logger, never `console.log`. |
| Metrics | Name, type (count, gauge, distribution), unit, tags. Say the source: trace span, log-based metric, or custom metric. Follow the names already in the codebase. |
| Dashboard widget | Widget type, query, and the NFR target drawn as a marker on the widget. |
| Monitor | Query, threshold equal to the NFR target, evaluation window, and who gets the alert. For availability and latency targets, prefer an SLO with a burn-rate alert when the tool offers one. |

Tag every metric and log so one client and one environment can be told
apart. Check the tag names the codebase already uses before you propose
one.

## One dashboard per project

Group every widget of the project in one dashboard, with one section per
NFR type. Name each widget after the NFR ID so the doc and the dashboard
point at each other.

## Build it

This skill only specifies the observability plan. Building the
dashboard, the monitors and the code changes is separate work.
