import unittest
import Grappa
import sql

class TestGrappa(unittest.TestCase):
    def setUp(self) -> None:
        CONFIG = Grappa.loadMainConfig("./test/test_main_config.json")
        args = type('MyClass', (object,), {'backend': ['mysql']})
        PLUGIN_CONF = Grappa.loadPluginConfig(CONFIG, args)
        #self.grappa = Grappa.Grappa(CONFIG, PLUGIN_CONF, Grappa.getPluginPath(), "test", args.backend[0])
        Grappa.GrappaLogging.init("/dev/null", "json", "info", "test", "mysql", CONFIG["log"]["rotation"])
        self.sqlPlugin = sql.Plugin(CONFIG, PLUGIN_CONF, Grappa.GrappaLogging.getLogger())
        pass

    def testGetTables(self):
        self.assertListEqual(self.sqlPlugin.getTableNames(), ["ram_usage"])

    def testGetTableColumns(self):
        self.assertEqual(self.sqlPlugin.getTableColumnNamesStr("ram_usage", "time"), "ram")

if __name__ == '__main__':
    unittest.main()