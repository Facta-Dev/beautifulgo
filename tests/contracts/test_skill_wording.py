"""Contract pins on the backend-go stack wording in the repo's docs.

The chi mandate must read the same way everywhere the stack is described:
the router is chi (REQUIRED), gin/echo are acceptable alternatives, fiber is
throughput-gateways-only. One file per surface, one concern per class.
"""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "skills" / "go-best-practices" / "SKILL.md"
STACK_REF = (
    REPO_ROOT
    / "skills"
    / "go-best-practices"
    / "references"
    / "backend-go-stack.md"
)
README = REPO_ROOT / "README.md"
CONFIG = REPO_ROOT / "lints" / ".golangci.yml"
CHECKER = REPO_ROOT / "scripts" / "check-examples.py"
CHECKER_TESTS = REPO_ROOT / "tests" / "test_check_examples.py"
OLD_SKILL_BAN = "No gin, echo, fiber, or chi"
OLD_README_BAN = "no gin/echo/fiber/chi"

CHI_PATH = "github.com/go-chi/chi/"
CHI_MOD = "github.com/go-chi/chi/v5"


def text_of(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def chi_mentions(path):
    """Word-boundary chi hits in one file (hyphen/slash count as boundaries)."""
    return len(re.findall(r"\bchi\b", text_of(path)))


class OldProhibitionRemoved(unittest.TestCase):
    """The stack no longer bans chi; nothing may still say it does."""

    def test_skill_no_longer_bans_chi(self):
        self.assertNotIn(OLD_SKILL_BAN, text_of(SKILL))

    def test_reference_no_longer_bans_chi(self):
        self.assertNotIn(OLD_SKILL_BAN, text_of(STACK_REF))

    def test_readme_routing_row_no_longer_bans_chi(self):
        body = text_of(README)
        self.assertNotIn(OLD_README_BAN, body)
        # Line-local: a routing line may not pair a standalone "no" with chi.
        for line in body.split("\n"):
            self.assertFalse(
                re.search(r"\bno\b.{0,40}\bchi\b", line),
                'README still phrases chi as banned: %r' % line,
           )


class ChiMandatePresent(unittest.TestCase):
    # Tolerant on purpose: a floor on chi mentions survives rewording drift,
    # while the exact strings are pinned on README in ExactReadmePins.
    def test_chi_mentioned_across_skill_files(self):
        total = chi_mentions(SKILL) + chi_mentions(STACK_REF)
        self.assertGreaterEqual(
            total, 3, "chi should be named in both skill surfaces"
        )


class ExactReadmePins(unittest.TestCase):
    """README pins are exact because this edit (and its contracts) landed here."""

    def test_routing_row_names_chi_required(self):
        body = text_of(README)
        self.assertIn(
            "| Routing | chi — REQUIRED, `net/http`-native (`github.com/go-chi/chi/v5`)",
            body,
        )
        self.assertIn("gin/echo acceptable alternatives", body)
        self.assertIn("fiber only for throughput-critical gateways", body)

    def test_migrations_row_names_golang_migrate(self):
        body = text_of(README)
        self.assertIn("| Migrations | golang-migrate", body)
        self.assertIn("never at server startup", body)
        self.assertIn("goose is the sanctioned alternative", body)


class Lockstep(unittest.TestCase):
    """Every enforcement surface names chi the same way."""

    def test_chi_prefix_pinned_in_all_checkers(self):
        # The config names the module; the checker and its tests pin the
        # bare prefix, which is what the forbidden-prefix tuple stores.
        self.assertIn(CHI_MOD, text_of(CONFIG))
        self.assertIn(CHI_PATH, text_of(CHECKER))
        self.assertIn(CHI_PATH, text_of(CHECKER_TESTS))


if __name__ == "__main__":
    unittest.main()