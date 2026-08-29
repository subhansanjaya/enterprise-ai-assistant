# Payment Gateway Recovery Runbook

Document ID: RUN-2025-004
Document Type: runbook
Department: payments
Access Level: internal
Created Date: 2025-03-10

## Purpose

This runbook describes the initial recovery procedure for payment
gateway failures.

## Step 1 — Check Payment API

Review:

- HTTP error rates
- Request latency
- Active instances
- Recent deployments

## Step 2 — Check Database Connections

Review PostgreSQL connection utilization.

If the connection pool is close to or at capacity, investigate
connection exhaustion.

## Step 3 — Check Transaction Service

Review transaction processing queues and error rates.

## Step 4 — Recovery

If connection exhaustion is confirmed:

1. Increase connection pool capacity where approved.
2. Restart affected application instances if required.
3. Monitor transaction processing.
4. Confirm error rates have returned to normal.

## Step 5 — Follow-up

Create an incident record and review whether capacity,
monitoring or alert thresholds need adjustment.