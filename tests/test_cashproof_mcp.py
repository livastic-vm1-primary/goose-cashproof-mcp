import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import CIRCLE_BASE8453, InputError, bounty_gate, handle_rpc, reconcile_receipts

SERVER = Path(__file__).resolve().parents[1] / "server.py"
PAYER = "0x" + "2"*40

def receipt(index=0, amount="0.005000", *, tx=None, independent=True):
    return {
        "chainId":8453, "token":CIRCLE_BASE8453,
        "txHash":tx or "0x"+"a"*64, "logIndex":index,
        "to":PAYER, "amountUSDC":amount, "finalityWitnessObserved":True,
        "independentExternalBuyerAndDeliveryEvidence":independent,
    }

def task(**kwargs):
    d=dict(originalGithubIssueState="open", maintainerConfirmsPayable=True,
        fundingProofIndependentFromListing=True,
        disclosedAIAssistancePermitted=True, oneRealBeneficialOwner=True)
    d.update(kwargs)
    return d

class TestReceiptArithmetic(unittest.TestCase):
    def test_exact_decimals_and_unattributed_separation(self):
        r=reconcile_receipts([receipt(0,"1.000000"),
                              receipt(1,"0.010000"),
                              receipt(2,"0.005000"),
                              receipt(3,"0.005000",independent=False)])
        self.assertEqual(r["grossClaimedFinalizedCircleBaseUSDC"],"1.020000")
        self.assertEqual(r["grossClaimedBuyerAndDeliveryAttributedUSDC"],"1.015000")
        self.assertEqual(r["receivedButDeliveryUnattributedUSDC"],"0.005000")
        self.assertFalse(r["independentlyVerifiedOnchain"])
        self.assertEqual(r["classification"],"OFFLINE_CALLER_DECLARATIONS_ONLY_NOT_AN_RPC_VERIFICATION")

    def test_no_double_credit_same_tx_log(self):
        with self.assertRaisesRegex(InputError,"duplicate"):
            reconcile_receipts([receipt(),receipt()])

    def test_same_tx_two_real_events_allowed(self):
        self.assertEqual(reconcile_receipts([receipt(index=1),receipt(index=2)])["distinctTransferEvents"],2)

    def test_duplicate_tx_mixed_case_blocked(self):
        a=receipt()
        b=receipt()
        b["txHash"]="0x"+"A"*64
        with self.assertRaisesRegex(InputError,"duplicate"):
            reconcile_receipts([a,b])

    def test_wrong_chain_canonical_token_refused(self):
        r=receipt();r["chainId"]=11155111
        with self.assertRaisesRegex(InputError,"Base"):reconcile_receipts([r])
        r=receipt();r["token"]="0x"+"f"*40
        with self.assertRaisesRegex(InputError,"canonical"):reconcile_receipts([r])

    def test_invalid_amount_types_and_decimals(self):
        for amt in [1,0,False,"1.1","1.0000000","-1.000000","0.000000","1e6"]:
            with self.subTest(amt=amt):
                r=receipt(amount=amt)
                with self.assertRaises(InputError):reconcile_receipts([r])

    def test_caller_finality_flag_required(self):
        r=receipt();r["finalityWitnessObserved"]=False
        with self.assertRaisesRegex(InputError,"finality"):reconcile_receipts([r])

    def test_receiver_must_be_valid_public_address(self):
        r=receipt();r["to"]="private"
        with self.assertRaisesRegex(InputError,"address"):reconcile_receipts([r])

    def test_event_index_bool_disallowed(self):
        r=receipt();r["logIndex"]=True
        with self.assertRaisesRegex(InputError,"logIndex"):reconcile_receipts([r])

    def test_external_delivery_flag_explicit(self):
        r=receipt();r.pop("independentExternalBuyerAndDeliveryEvidence")
        with self.assertRaisesRegex(InputError,"classify"):reconcile_receipts([r])

    def test_bounded_records(self):
        with self.assertRaisesRegex(InputError,"64"):reconcile_receipts([receipt(i) for i in range(65)])

class TestBountyUntrustedSource(unittest.TestCase):
    def test_open_claimable_only_review_not_cash(self):
        result=bounty_gate(task())
        self.assertEqual(result["status"],"REVIEW_PAID_SCOPE_NOT_AN_AWARD")
        self.assertEqual(result["actualEarnedUSDC"],"0.000000")
    def test_closed_has_hard_stop(self):
        self.assertEqual(bounty_gate(task(originalGithubIssueState="closed"))["status"],"SKIP_CLOSED")
    def test_unauthenticated_funds_are_not_a_job(self):
        self.assertEqual(bounty_gate(task(fundingProofIndependentFromListing=False))["status"],"HOLD_UNFUNDED_OR_UNCONFIRMED")
    def test_no_ai_policy_and_owner_mismatch_block(self):
        for k in ("disclosedAIAssistancePermitted","oneRealBeneficialOwner"):
            with self.subTest(k=k):
                self.assertEqual(bounty_gate(task(**{k:False}))["status"],"STOP_ELIGIBILITY")
    def test_missing_flag_not_inferred(self):
        d=task();d.pop("maintainerConfirmsPayable")
        with self.assertRaises(InputError):bounty_gate(d)

class TestMCPTransport(unittest.TestCase):
    def test_initialize_lists_two_tools(self):
        r=handle_rpc({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}})
        self.assertEqual(r["result"]["serverInfo"]["name"],"goose-cashproof-mcp")
        self.assertIn("2025",r["result"]["protocolVersion"])
        r=handle_rpc({"jsonrpc":"2.0","id":2,"method":"tools/list"})
        self.assertEqual({a["name"] for a in r["result"]["tools"]},{"reconcile_base_usdc_receipts","triage_public_bounty"})

    def test_stdio_jsonrpc_real_subprocess_no_extraneous_stdout(self):
        cmds=[
            {"jsonrpc":"2.0","id":7,"method":"initialize","params":{"protocolVersion":"2025-06-18"}},
            {"jsonrpc":"2.0","method":"notifications/initialized"},
            {"jsonrpc":"2.0","id":8,"method":"tools/list"},
            {"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"name":"reconcile_base_usdc_receipts","arguments":{"receipts":[receipt()]}}},
            {"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"triage_public_bounty","arguments":{"task":task()}}},
        ]
        r=subprocess.run([sys.executable,str(SERVER)], input="\n".join(json.dumps(x) for x in cmds)+"\n",
                         text=True,capture_output=True,timeout=6,check=True)
        self.assertEqual(r.stderr,"")
        lines=[json.loads(x) for x in r.stdout.splitlines()]
        self.assertEqual([x["id"] for x in lines],[7,8,9,10])
        self.assertEqual(lines[2]["result"]["isError"],False)
        self.assertEqual(lines[3]["result"]["isError"],False)
        obj=json.loads(lines[2]["result"]["content"][0]["text"])
        self.assertFalse(obj["independentlyVerifiedOnchain"])

    def test_unknown_tool_safe_error(self):
        d=handle_rpc({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"shell_exec","arguments":{}}})
        self.assertIn("error",d)

    def test_untrusted_input_yields_tool_error_no_code_exec(self):
        d=handle_rpc({"jsonrpc":"2.0","id":4,"method":"tools/call",
                      "params":{"name":"reconcile_base_usdc_receipts","arguments":{"receipts":[{"__proto__":"oops"}]}}})
        self.assertTrue(d["result"]["isError"])

if __name__=="__main__":unittest.main()
