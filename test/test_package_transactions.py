"""Package transaction ordering for the target install."""

import sys
import types
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "configs/airootfs/usr/share/omarchy-iso"))
sys.modules.setdefault(
    "orchestrator.archinstall_adapter", types.ModuleType("orchestrator.archinstall_adapter")
)

from orchestrator import phases_impl  # noqa: E402


class RecordingInstaller:
    def __init__(self):
        self.transactions = []

    def add_additional_packages(self, packages):
        self.transactions.append(packages)


class PackageTransactionTest(unittest.TestCase):
    def install(self, tailscale=False):
        installer = RecordingInstaller()
        ctx = types.SimpleNamespace(
            tailscale_authkey_path=Path("/tmp/authkey") if tailscale else None
        )

        with (
            mock.patch.object(phases_impl, "_early_bootstrap_packages", return_value=["bootstrap"]),
            mock.patch.object(phases_impl, "_early_user_seed_packages", return_value=["user-seed"]),
            mock.patch.object(phases_impl, "_runtime_package_list", return_value=["runtime", "base"]),
            mock.patch.object(phases_impl, "info"),
        ):
            phases_impl._install_omarchy_packages(ctx, installer)

        return installer.transactions

    def test_keeps_luarocks_before_user_seed_while_using_two_transactions(self):
        self.assertEqual(
            self.install(),
            [
                ["bootstrap", "lua51", "luarocks"],
                ["user-seed", "runtime", "base"],
            ],
        )

    def test_adds_tailscale_to_the_runtime_transaction(self):
        self.assertEqual(
            self.install(tailscale=True)[1],
            ["user-seed", "runtime", "base", "tailscale"],
        )


if __name__ == "__main__":
    unittest.main()
