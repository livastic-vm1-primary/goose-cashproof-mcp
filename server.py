#!/usr/bin/env python3
"""A local-only, read-only MCP extension for goose: offline payment evidence gates.

No RPC requests, signatures, wallet access, terminal commands or files. Every
receipt is explicitly marked caller-supplied, NOT independently chain verified.
MCP stdio: one JSON-RPC object per line; stdout is protocol responses only.
"""
from __future__ import annotations
from decimal import Decimal
import json
import re
import sys
from typing import Any

VERSION = "0.1.0"
PROTOCOL_VERSION = "2025-06-18"
CIRCLE_BASE8453 = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
TX = re.compile(r"0x[a-fA-F0-9]{64}\Z")
WALLET = re.compile(r"0x[a-fA-F0-9]{40}\Z")
USDC = re.compile(r"(?:0|[1-9][0-9]*)\.[0-9]{6}\Z")
MAX_LINE = 65536
MAX_RECEIPTS = 64


class InputError(ValueError):
    pass


def verified_public_address(value: Any) -> str:
    if not isinstance(value, str) or not WALLET.fullmatch(value):
        raise InputError("recipient must be a public 20-byte EVM address")
    return value.lower()


def reconcile_receipts(receipts: Any) -> dict[str, Any]:
    if not isinstance(receipts, list) or len(receipts) > MAX_RECEIPTS:
        raise InputError("receipts must be a list of at most 64")
    seen: set[tuple[str, int]] = set()
    settled = Decimal("0.000000")
    attributed = Decimal("0.000000")
    for i, v in enumerate(receipts):
        if not isinstance(v, dict) or type(v.get("chainId")) is not int or v.get("chainId") != 8453:
            raise InputError("each event must explicitly use Base chain 8453")
        if not isinstance(v.get("token"), str) or v["token"].lower() != CIRCLE_BASE8453:
            raise InputError("only canonical Base Circle USDC allowed")
        h = v.get("txHash")
        if not isinstance(h, str) or not TX.fullmatch(h):
            raise InputError("invalid 32-byte public txHash")
        idx = v.get("logIndex")
        if type(idx) is not int or idx < 0 or idx > 10**9:
            raise InputError("invalid ERC-20 Transfer logIndex")
        verified_public_address(v.get("to"))
        receipt_id = (h.lower(), idx)
        if receipt_id in seen:
            raise InputError("duplicate transaction log (no double credit)")
        seen.add(receipt_id)
        amount = v.get("amountUSDC")
        if not isinstance(amount, str) or not USDC.fullmatch(amount):
            raise InputError("amount must be a nonnegative exact 6-decimal USDC string")
        d = Decimal(amount)
        if d <= 0 or v.get("finalityWitnessObserved") is not True:
            raise InputError("positive amount and explicit caller finality witness required")
        buyer = v.get("independentExternalBuyerAndDeliveryEvidence")
        if type(buyer) is not bool:
            raise InputError("must explicitly classify external buyer plus delivery as true or false")
        settled += d
        if buyer:
            attributed += d
    return {
        "classification": "OFFLINE_CALLER_DECLARATIONS_ONLY_NOT_AN_RPC_VERIFICATION",
        "distinctTransferEvents": len(seen),
        "grossClaimedFinalizedCircleBaseUSDC": f"{settled:.6f}",
        "grossClaimedBuyerAndDeliveryAttributedUSDC": f"{attributed:.6f}",
        "receivedButDeliveryUnattributedUSDC": f"{settled-attributed:.6f}",
        "realBankCashoutUSD": None,
        "afterCostNetProfitUSD": None,
        "independentlyVerifiedOnchain": False,
        "permittedDecision": "INCONCLUSIVE_PENDING_INDEPENDENT_ORIGINAL_CHAIN_SOURCE",
        "warning": "Caller-supplied flags and tx hashes are not chain verification, proof of beneficial owner, receipt of fiat, invoice, or a signed contract.",
    }


def bounty_gate(task: Any) -> dict[str, Any]:
    if not isinstance(task, dict):
        raise InputError("task must be a JSON object")
    state = task.get("originalGithubIssueState")
    if state not in ("open", "closed", "unknown"):
        raise InputError("state must be open, closed or unknown")
    maintainer = task.get("maintainerConfirmsPayable")
    source = task.get("fundingProofIndependentFromListing")
    ai_ok = task.get("disclosedAIAssistancePermitted")
    real_owner = task.get("oneRealBeneficialOwner")
    for k in (maintainer, source, ai_ok, real_owner):
        if type(k) is not bool:
            raise InputError("all four eligibility flags must be explicit booleans")
    if state=="closed":
        result="SKIP_CLOSED"
    elif state!="open":
        result="STOP_UNVERIFIED_SOURCE"
    elif not ai_ok or not real_owner:
        result="STOP_ELIGIBILITY"
    elif not maintainer or not source:
        result="HOLD_UNFUNDED_OR_UNCONFIRMED"
    else:
        result="REVIEW_PAID_SCOPE_NOT_AN_AWARD"
    return {
        "status": result, "actualEarnedUSDC": "0.000000",
        "independentlyVerifiedFirstParty": False,
        "warning": "Only original-source checks, a genuine independent buyer-approved contract, actual delivery and a finalized original payee transfer can establish earned money.",
    }


RECONCILE_SCHEMA = {
    "type": "object",
    "properties": {"receipts": {"type": "array", "maxItems": MAX_RECEIPTS,
                                "description": "Untrusted, caller-supplied public Base ERC-20 receipt declarations; no private keys"}},
    "required": ["receipts"], "additionalProperties": False,
}
GATE_SCHEMA = {
    "type": "object",
    "properties": {
        "task": {"type": "object", "required": [
            "originalGithubIssueState", "maintainerConfirmsPayable",
            "fundingProofIndependentFromListing", "disclosedAIAssistancePermitted",
            "oneRealBeneficialOwner"
        ]}},
    "required": ["task"], "additionalProperties": False,
}
TOOLS = [
    {"name":"reconcile_base_usdc_receipts",
     "description":"Offline Decimal/dedup audit of public, caller-declared Base Circle USDC transfers. NEVER independently proves chain or commercial delivery. No signing, network or files.",
     "inputSchema": RECONCILE_SCHEMA},
    {"name":"triage_public_bounty",
     "description":"Classify untrusted, caller-declared GitHub bounty requirements without claiming award, escrow or real payment; original-source verification remains buyer's responsibility.",
     "inputSchema": GATE_SCHEMA},
]


def successful(id_: Any, result: Any) -> dict:
    return {"jsonrpc":"2.0", "id":id_, "result":result}


def error(id_: Any, code: int, message: str) -> dict:
    return {"jsonrpc":"2.0", "id":id_, "error":{"code":code,"message":message}}


def handle_rpc(message: Any) -> dict | None:
    if not isinstance(message,dict):
        return error(None,-32600,"MCP requires one JSON-RPC request object")
    id_=message.get("id")
    if message.get("jsonrpc")!="2.0":
        return error(id_,-32600,"Invalid JSON-RPC version")
    method=message.get("method")
    if method=="notifications/initialized":
        return None
    if "id" not in message:
        return None
    if method=="ping":
        return successful(id_,{})
    if method=="initialize":
        return successful(id_,{
            "protocolVersion":PROTOCOL_VERSION,
            "capabilities":{"tools":{"listChanged":False}},
            "serverInfo":{"name":"goose-cashproof-mcp","version":VERSION},
            "instructions":"Local offline evidence triage only. Trust original verified payment chain sources, never this caller-supplied fixture as real settlement.",
        })
    if method=="tools/list":
        return successful(id_,{"tools":TOOLS})
    if method=="tools/call":
        params=message.get("params")
        if not isinstance(params,dict):
            return error(id_,-32602,"tools/call requires params")
        name=params.get("name")
        args=params.get("arguments")
        if not isinstance(args,dict):
            return error(id_,-32602,"tools/call requires an arguments object")
        try:
            if name=="reconcile_base_usdc_receipts":
                if set(args)!={"receipts"}:
                    raise InputError("unexpected or missing arguments")
                output=reconcile_receipts(args["receipts"])
            elif name=="triage_public_bounty":
                if set(args)!={"task"}:
                    raise InputError("unexpected or missing arguments")
                output=bounty_gate(args["task"])
            else:
                return error(id_,-32602,"unknown tool")
        except InputError as e:
            return successful(id_,{"content":[{"type":"text","text":str(e)}],"isError":True})
        return successful(id_,{"content":[{"type":"text","text":json.dumps(output,separators=(",",":"))}],"isError":False})
    return error(id_,-32601,"Method not found")


def main() -> int:
    buf=sys.stdin.buffer
    out=sys.stdout.buffer
    while True:
        line=buf.readline(MAX_LINE+1)
        if not line:
            return 0
        if len(line)>MAX_LINE or not line.endswith(b"\n"):
            # Abort; do not consume or log arbitrary oversized untrusted input.
            return 2
        try:
            request=json.loads(line)
        except (ValueError,UnicodeDecodeError):
            response=error(None,-32700,"Parse error")
        else:
            response=handle_rpc(request)
        if response is not None:
            out.write((json.dumps(response,separators=(",",":"))+"\n").encode("utf8"))
            out.flush()


if __name__=="__main__":
    raise SystemExit(main())
