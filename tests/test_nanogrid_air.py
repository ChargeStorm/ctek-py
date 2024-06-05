import unittest
from unittest.mock import patch

from ctek.nanogrid_air import (
    ChargeboxInfo,
    DeviceInfo,
    DeviceStatus,
    EVSEData,
    EVSEInfo,
    MeterData,
    MeterInfo,
    MeterRawData,
    NanogridAir,
    OTAInfo,
)


class TestNanogridAir(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_status(self):
        async def mock_fetch_data(endpoint):
            return {
                "deviceInfo": {
                    "serial": "123456",
                    "firmware": "v1.0",
                    "mac": "00:11:22:33:44:55",
                },
                "chargeboxInfo": {
                    "identity": "abc",
                    "serial": "789",
                    "firmware": "v2.0",
                    "endpoint": "http://example.com",
                    "port": 8080,
                    "state": "connected",
                },
                "meterInfo": {"vendor": "vendor", "type": "type", "id": "id"},
                "otaInfo": {"status": 1, "version": "v2.1", "progress": 50},
            }

        with patch.object(NanogridAir, "_fetch_data", side_effect=mock_fetch_data):
            nanogrid_air = NanogridAir()
            status = await nanogrid_air.fetch_status()

            self.assertIsInstance(status, DeviceStatus)
            self.assertEqual(status.device_info.serial, "123456")
            self.assertEqual(status.chargebox_info.serial, "789")
            self.assertEqual(status.meter_info.vendor, "vendor")
            self.assertEqual(status.ota_info.status, 1)

    async def test_fetch_meter_data(self):
        async def mock_fetch_data(endpoint):
            return {
                "activePowerIn": 100,
                "activePowerOut": 50,
                "current": [1, 2, 3],
                "voltage": [220, 230, 240],
                "totalEnergyActiveImport": 500,
                "totalEnergyActiveExport": 200,
            }

        with patch.object(NanogridAir, "_fetch_data", side_effect=mock_fetch_data):
            nanogrid_air = NanogridAir()
            meter_data = await nanogrid_air.fetch_meter_data()

            self.assertIsInstance(meter_data, MeterData)
            self.assertEqual(meter_data.active_power_in, 100)
            self.assertEqual(meter_data.total_energy_active_import, 500)

    async def test_fetch_mac(self):
        async def mock_fetch_status():
            return DeviceStatus(
                device_info=DeviceInfo(
                    serial="123456", firmware="v1.0", mac="00:11:22:33:44:55"
                ),
                chargebox_info=ChargeboxInfo(
                    identity="abc",
                    serial="789",
                    firmware="v2.0",
                    endpoint="http://example.com",
                    port=8080,
                    state="connected",
                ),
                meter_info=MeterInfo(vendor="vendor", type="type", id="id"),
                ota_info=OTAInfo(status=1, version="v2.1", progress=50),
            )

        with patch.object(NanogridAir, "fetch_status", side_effect=mock_fetch_status):
            nanogrid_air = NanogridAir()
            mac = await nanogrid_air.fetch_mac()

            self.assertEqual(mac, "00:11:22:33:44:55")

    async def test_fetch_meterraw(self):
        async def mock_fetch_data(endpoint):
            return {
                "0": {"result": "OK", "cpu_time_ms": 100, "len": 10, "data": "abcdef"},
                "1": {
                    "result": "ERROR",
                    "cpu_time_ms": 200,
                    "len": 20,
                    "data": "123456",
                },
            }

        with patch.object(NanogridAir, "_fetch_data", side_effect=mock_fetch_data):
            nanogrid_air = NanogridAir()
            meter_raw_data = await nanogrid_air.fetch_meterraw()

            self.assertIsInstance(meter_raw_data, list)
            self.assertEqual(len(meter_raw_data), 2)
            self.assertIsInstance(meter_raw_data[0], MeterRawData)
            self.assertEqual(meter_raw_data[0].result, "OK")

    async def test_fetch_evse(self):
        async def mock_fetch_data(endpoint):
            return {
                "0": {
                    "cb_id": "cb1",
                    "connection_status": "connected",
                    "evse": [{"id": 1, "state": 1, "current": [10, 20, 30]}],
                },
                "1": {
                    "cb_id": "cb2",
                    "connection_status": "disconnected",
                    "evse": [{"id": 2, "state": 0, "current": [5, 10, 15]}],
                },
            }

        with patch.object(NanogridAir, "_fetch_data", side_effect=mock_fetch_data):
            nanogrid_air = NanogridAir()
            evse_data = await nanogrid_air.fetch_evse()

            self.assertIsInstance(evse_data, list)
            self.assertEqual(len(evse_data), 2)
            self.assertIsInstance(evse_data[0], EVSEData)
            self.assertEqual(evse_data[0].cb_id, "cb1")
            self.assertEqual(evse_data[0].connection_status, "connected")
            self.assertIsInstance(evse_data[0].evse[0], EVSEInfo)
            self.assertEqual(evse_data[0].evse[0].id, 1)
