# rembish.org

Personal website / portfolio. Public repo.

## Repo Structure

This repo has a private sibling: `../rembish_org_ops/`

- **This repo (public):** Application code, templates, local dev setup
- **OPS repo (private):** Production infra, secrets, deploy runbooks, main AI instructions

## Rules

- No production secrets, resource IDs, or deploy credentials here
- No real Cloud Run URLs, GCP project numbers, or access tokens
- Deployment docs here are architecture-only (no real identifiers)

## For AI

Main instructions are in `../rembish_org_ops/CLAUDE.md`. This file exists only for repo identification and public/private boundary enforcement.

