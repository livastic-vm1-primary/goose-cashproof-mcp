# goose CashProof — non-custodial MCP evidence guardrails

**Public prototype, NOT a production payment oracle, paid goose grant, verified wallet, or customer sale.** One genuine South Korea-based beneficial human owner, AI-assisted engineering under project display name PaperPilot Tools.

Goose supports local standard-I/O extensions via the Model Context Protocol (MCP). This Python 3.11+ standard-library prototype exposes two safe offline tools:

1. **reconcile_base_usdc_receipts:** exact Decimal arithmetic on up to 64 caller-supplied Base 8453 native Circle USDC ERC20 transfer events. Reject duplicate txHash/logIndex combinations, incorrect chain/token/recipient, malformed amounts, and claims without explicit finality flags. Separately totals claimed received tokens and explicitly externally buyer-and-delivery-attributed receipts.
2. **triage_public_bounty:** source/AI eligibility/funding checklist which never treats a nominal quoted bounty as earned money.

**A caller's supplied "finality observed" boolean is NOT chain verification**. The server has NO network, no account access, no key retrieval, no payment APIs, no transaction signing, no private financial data and no file writes. Its outputs explicitly state independentlyVerifiedOnchain=false, actual fiat/net profit unknown.

## Reproduce locally

    python3 -B -m unittest discover -s tests -v

    python3 -B server.py

**20/20 source-level and JSON-RPC stdio process tests PASS on VM1.** A real subprocess exchanges initialize, tools/list, tools/call and notification messages without extraneous stdout. Tested ONLY at the documented MCP transport level, not yet inside an actual goose Desktop or CLI session.

Example manually generating the first two protocol requests:

    printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}' '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 -B server.py

In a trusted existing goose installation, the official goose configure > Add Extension > Command-line Extension workflow can point to python3 and the absolute checked-out server.py. See goose_extension.yaml.example. This configuration has **not** been deployed on any active VM goose instance or production agent. Operators must consent before enabling an extension.

## Prior authentic (separate business) operator evidence

A separate public [four-receipt study](https://github.com/livastic-vm1-primary/usdc-payout-proof-cases/blob/main/cases/four-genuine-base-usdc-incoming-vs-attributed-sales-20261020.md) distinguishes 1.020000 USDC finalized across four historical Base native Circle Transfer events from 1.015000 USDC of independently sponsored/paid-delivered work, with 0.005000 USDC correctly flagged not attributable to a proven particular successful paid API call. These were earned by **other pre-existing** experiments, NOT by this repository or goose.

Separate [SlothProof](https://github.com/livastic-vm1-primary/slothproof-bounty-gate) demonstrates a local open-weight AI source-first stale bounty gate and has zero separately paid customers.

## Open-source research grant

[PROPOSAL.md](PROPOSAL.md) outlines a 12-month, four-checkpoint research plan for the [goose $100,000 grant programme](https://goose-docs.ai/grants/). This is conditional sponsor potential ONLY. This repo has **no accepted goose grant, no payout and no contract**. No legal identity or bank credentials have been fabricated. Plans include read-only independent chain finality after permissioned human review, explicit agent guardrails, actual goose integration, open adversarial source benchmarks and documentation; NONE of those later milestones is asserted already complete.

References: [goose custom extensions](https://goose-docs.ai/docs/tutorials/custom-extensions/), [goose configuration](https://goose-docs.ai/docs/getting-started/using-extensions/), [MCP stdio](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports).

MIT License, © 2026 PaperPilot Tools. All code disclosed as substantially AI-assisted and original to this one economic owner.
