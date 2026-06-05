# Archiver Bot

A full-featured Telegram bot for archiving, forwarding, and managing messages across channels, groups, and private chats — with duplicate detection, group moderation tools, AI features, and a premium tier.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

**Python bot (Render deployment):**
- `cd bot && pip install -r requirements.txt` — install bot dependencies
- `cd bot && python main.py` — run the bot locally
- `cd bot && python worker.py` — run the background job worker
- Copy `bot/.env.example` to `bot/.env` and fill in all values before running locally

## Stack

**Node.js monorepo (Mini App frontend — built in later parts):**
- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`

**Python bot backend:**
- python-telegram-bot v21 (async, polling mode)
- Telethon (MTProto user account login)
- Motor (async MongoDB driver)
- Redis (aioredis) — job queues, rate limiting, subscription cache
- aiohttp — health check HTTP server (required by Render)

**Infrastructure (Render free tier):**
- Web Service — bot process (polling + health endpoint)
- Background Worker — job processor for forward/dedupe/download jobs
- Cron Job — keep-alive ping every 14 minutes
- Redis — Render managed Redis (free tier)
- MongoDB Atlas — external free cluster (512MB)

## Where things live

- `bot/` — Python bot (all 8 parts live here)
  - `bot/main.py` — entry point, registers all handlers, starts polling
  - `bot/worker.py` — background job processor
  - `bot/config.py` — all env vars (source of truth for config)
  - `bot/database/` — MongoDB connection + document schemas
  - `bot/handlers/` — Telegram command/callback handlers
  - `bot/middleware/` — subscription gate (runs before every command)
  - `bot/services/` — Redis client, subscription checker
  - `bot/utils/` — shared helper functions
  - `bot/health.py` — aiohttp health check server
  - `bot/.env.example` — template for all required env vars
- `render.yaml` — Render deployment config (web + worker + cron + redis)

## Architecture decisions

- **Polling not webhooks** — Render free tier spins down; polling is simpler and more reliable. A keep-alive cron pings /health every 14 min to prevent cold starts.
- **Subscription gate as middleware** — every command passes through `subscription_gate()` in `bot/middleware/subscription.py` before executing. Admins bypass the gate.
- **Redis caches subscription checks** — Telegram's `getChatMember` is rate-limited; results are cached 5 min per user to avoid hammering the API.
- **Job queue pattern** — heavy work (forwarding, deduplication, downloads) is pushed to Redis queues and processed by the worker, keeping the bot responsive.
- **MongoDB document design** — one collection per entity type (users, sessions, chats, jobs, logs, premium). All indexed on user_id for fast per-user queries.

## Product

8-part Telegram bot:
- **Part 1 (done)** — Foundation: DB, Redis, subscription gate, /start, /help, admin commands
- **Part 2** — User account login via MTProto (Telethon), session management, /mychats
- **Part 3** — Archiver core: forward engine, live/historical forwarding, edited message sync
- **Part 4** — Duplicate detector: file_unique_id, size, cryptographic hash (premium)
- **Part 5** — Channel/group join manager: Q&A gating, backup channel requirement
- **Part 6** — Group moderation: ban timers, magic words, member lists, admin logs
- **Part 7** — AI & search: history search, audio transcription, AI translation
- **Part 8** — Premium system & restricted content download/reupload

## User preferences

- Deploying on Render (free tier services)
- Python + Telethon + python-telegram-bot stack
- MongoDB Atlas (free) for database
- Redis (Render managed) for queues
- All free services where possible
- Build in 8 ordered parts

## Gotchas

- Never call `pnpm dev` at workspace root — use workflow commands or `restart_workflow`.
- Bot runs in polling mode (not webhook) because Render free tier spins down services.
- The keep-alive cron in render.yaml must use the actual deployed URL — update `archiver-bot.onrender.com` to your real Render URL after first deploy.
- Admin user IDs must be comma-separated integers in `ADMIN_USER_IDS` env var.
- Users must `/start` the bot at least once before `/addpremium` can find them.
- `MANDATORY_CHANNEL_ID` can be either a username (`@channel`) or numeric ID (`-1001234567890`).

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
- See `bot/.env.example` for all required environment variables
- See `render.yaml` for the full Render deployment configuration
