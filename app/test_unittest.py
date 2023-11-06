import unittest
import Grappa
import sql
import datetime

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

    def testQuery(self):
        request = {"targets": [{"target": "ram_usage", "payload": {}}], "range": {"from": str((datetime.datetime.fromtimestamp(1699266108) - datetime.timedelta(hours=2)).isoformat()) + ".0Z", "to": str(datetime.datetime.fromtimestamp(1699266108).isoformat()) + ".0Z"}}
        self.assertEqual(self.sqlPlugin.queryDb(request), [{'target': 'ram_usage', 'datapoints': [[50.0, 1699266108000], [60.0, 1699266109000], [70.0, 1699266110000]]}])

if __name__ == '__main__':
    unittest.main()