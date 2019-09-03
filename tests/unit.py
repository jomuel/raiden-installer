#!/usr/bin/env python

import unittest
import tempfile
from pathlib import Path

from raiden_installer.account import Account
from raiden_installer.base import RaidenConfigurationFile, PassphraseFile
from raiden_installer.ethereum_rpc import make_web3_provider
from raiden_installer.network import Network


class AccountTestCase(unittest.TestCase):
    def setUp(self):
        Account.DEFAULT_KEYSTORE_FOLDER = tempfile.gettempdir()

        self.account = Account.create(passphrase="test_password")

    def test_account_can_get_address(self):
        self.assertIsNotNone(self.account.address)

    def test_can_not_get_private_key_without_passphrase(self):
        empty_account = Account("/invalid_folder")

        with self.assertRaises(ValueError):
            empty_account.private_key

    def test_can_get_web3_provider(self):
        web3_provider = make_web3_provider("http://localhost:8545", self.account)
        self.assertIsNotNone(web3_provider)

    def tearDown(self):
        self.account.keystore_file_path.unlink()


@unittest.skip("Still need to make mock functions for w3")
class RaidenConfigurationTestCase(unittest.TestCase):
    def setUp(self):
        temp_folder_path = Path(tempfile.gettempdir())
        RaidenConfigurationFile.FOLDER_PATH = temp_folder_path

        self.account = Account.create(passphrase="test_raiden_config")
        self.network = Network.get_by_name("goerli")
        self.ethereum_client_rpc_endpoint = "http://localhost:8545"

        self.configuration_file = RaidenConfigurationFile(
            account=self.account,
            network=self.network,
            ethereum_client_rpc_endpoint=self.ethereum_client_rpc_endpoint,
            token=self.token,
        )

        passphrase_file = PassphraseFile(self.configuration_file.passphrase_file_path)
        passphrase_file.store(self.account.passphrase)

    def test_can_save_configuration(self):
        self.configuration_file.save()
        self.assertTrue(self.configuration_file.path.exists())

    def test_can_create_configuration(self):
        self.configuration_file.save()
        all_configs = RaidenConfigurationFile.get_available_configurations()
        self.assertEqual(len(all_configs), 1)

    def tearDown(self):
        for config in RaidenConfigurationFile.get_available_configurations():
            config.passphrase_file_path.unlink()
            config.path.unlink()


if __name__ == "__main__":
    unittest.main()
