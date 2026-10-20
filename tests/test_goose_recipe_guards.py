"""Guard intentionally trust-sensitive goose recipe before publication."""
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]

class OfficialGooseRecipeGuards(unittest.TestCase):
    def test_recipe_explicit_readonly_mcp_entrypoint(self):
        text=(ROOT/"recipes"/"goose-cashproof-offline.yaml").read_text(encoding="utf8")
        self.assertEqual(text.count("  - type: stdio"),1)
        self.assertIn("    cmd: python3\n    args:\n      - server.py",text)
        self.assertIn("    available_tools:\n      - reconcile_base_usdc_receipts\n      - triage_public_bounty",text)
        self.assertNotIn("    cmd: sh",text)
        self.assertNotIn("    cmd: bash",text)
        self.assertNotIn("    cmd: curl",text)
        self.assertNotIn("retry:",text)
        self.assertNotIn("GOOSE_API_KEY",text)
    def test_recipe_does_not_ask_llm_to_spend_or_autobuy(self):
        text=(ROOT/"recipes"/"goose-cashproof-offline.yaml").read_text()
        self.assertIn("never sign/send/approve funds",text)
        self.assertIn("Do not call the tools until a human explicitly supplies",text)
        self.assertIn("NOT chain",text)
        self.assertIn("cmd: python3",text)
    def test_verified_recipe_targets_existing_source_only(self):
        self.assertTrue((ROOT/"server.py").is_file())
        self.assertTrue((ROOT/"tests/test_cashproof_mcp.py").is_file())
        self.assertTrue((ROOT/"PROPOSAL.md").is_file())
if __name__ == "__main__":unittest.main()
