# Official goose CLI validation — v1.55.0

**Completed 2026-10-20 KST, original VM1, one real human beneficial owner.**

Original official source: https://github.com/aaif-goose/goose/releases/tag/v1.55.0

We downloaded the **official** x86_64 Linux musl asset into a separate isolated VM1 work folder, verified the original release SHA-256 `599b35f8a91f4e9ff728f92a0249995b632fd262ba9eb6165a59b86e5d221f61` for `goose-x86_64-unknown-linux-musl.tar.bz2`, validated it contains a standalone goose executable, and used a separate test-only HOME and XDG_CONFIG_HOME. No system-wide installation or production goose settings were changed.

The official goose binary reported **1.55.0**. In the original CashProof source checkout we ran:

```sh
goose --version
goose recipe validate recipes/goose-cashproof-offline.yaml
goose run --recipe recipes/goose-cashproof-offline.yaml --render-recipe
python3 -B -m unittest discover -s tests -q
```

**Observed:** the native goose recipe validator printed `✓ recipe file is valid`; recipe-only render displayed one original stdio extension with `cmd: python3`, `args: [server.py]`, and the two CashProof allowlisted read-only tools `reconcile_base_usdc_receipts` and `triage_public_bounty`. Separately, actual MCP JSON-RPC stdio subprocess tests passed and no blockchain RPC, user identity, signatures, gas, provider key, or real customer payment was involved.

**Important untested boundary:** `--render-recipe` parses configuration but does not start an LLM agent or invoke CashProof from a real goose Desktop/CLI chat. Native actual goose-to-MCP tool execution with an independently authorized user-selected model provider is **NOT yet proven**. Do not market this as completed production goose integration.

**Security:** goose recipe YAML can name a local executable and may spawn it when a user runs a recipe. This specific checked-in file contains only the user-reviewable local `python3 server.py`, no shell-retry commands, wallet tools, credential environment variables or HTTP MCP servers. Never execute arbitrary internet recipes without reviewing their commands. The native validation and recipe render used an isolated HOME to protect any configured production sessions.

**Revenue:** the already-submitted annual conditional goose grant application is not an award. Public code, successful validation, a quote, a grant application, or a CLI installation create **0 USD/USDC actual cash**.
