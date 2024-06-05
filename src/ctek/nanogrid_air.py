import socket
from dataclasses import dataclass, field
from typing import Any

import aiohttp


@dataclass
class DeviceInfo:
    serial: str
    firmware: str
    mac: str


@dataclass
class ChargeboxInfo:
    identity: str
    serial: str
    firmware: str
    endpoint: str
    port: int
    state: str


@dataclass
class MeterInfo:
    vendor: str
    type: str
    id: str


@dataclass
class OTAInfo:
    status: int
    version: str
    progress: int


@dataclass
class DeviceStatus:
    device_info: DeviceInfo
    chargebox_info: ChargeboxInfo
    meter_info: MeterInfo
    ota_info: OTAInfo


@dataclass
class MeterData:
    active_power_in: float
    active_power_out: float
    current: list[float]
    voltage: list[float]
    total_energy_active_import: int
    total_energy_active_export: int


@dataclass
class MeterRawData:
    result: str
    cpu_time_ms: int
    length: int
    data: str


@dataclass
class EVSEInfo:
    id: int
    state: int
    current: list[float]


@dataclass
class EVSEData:
    cb_id: str
    connection_status: str
    evse: list[EVSEInfo] = field(default_factory=list)


@dataclass
class NanogridAir:
    device_ip: str | None = None
    _initialized: bool = False

    async def get_ip(self, hostname: str = "ctek-ng-air.local") -> str | None:
        try:
            ip = socket.gethostbyname(hostname)
            if ip:
                return ip
        except socket.gaierror:
            return None
        return None

    async def _initialize(self) -> None:
        if not self._initialized:
            if not self.device_ip:
                self.device_ip = await self.get_ip()
            self._initialized = True

    async def _fetch_data(self, endpoint: str) -> dict[str, Any]:
        await self._initialize()
        url = f"http://{self.device_ip}/{endpoint}/"
        async with aiohttp.ClientSession() as session, session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            if isinstance(data, list):
                return {str(idx): item for idx, item in enumerate(data)}
            elif isinstance(data, dict):
                return data
            else:
                raise ValueError("Unexpected data type received")

    async def fetch_status(self) -> DeviceStatus:
        data: dict[str, Any] = await self._fetch_data("status")
        return DeviceStatus(
            device_info=DeviceInfo(**data["deviceInfo"]),
            chargebox_info=ChargeboxInfo(**data["chargeboxInfo"]),
            meter_info=MeterInfo(**data["meterInfo"]),
            ota_info=OTAInfo(**data["otaInfo"]),
        )

    async def fetch_mac(self) -> str:
        status = await self.fetch_status()
        return status.device_info.mac

    async def fetch_meter_data(self) -> MeterData:
        data: dict[str, Any] = await self._fetch_data("meter")
        return MeterData(
            active_power_in=data["activePowerIn"],
            active_power_out=data["activePowerOut"],
            current=data["current"],
            voltage=data["voltage"],
            total_energy_active_import=data["totalEnergyActiveImport"],
            total_energy_active_export=data["totalEnergyActiveExport"],
        )

    async def fetch_meterraw(self) -> list[MeterRawData]:
        data = await self._fetch_data("meterraw")
        return [
            MeterRawData(
                result=item["result"],
                cpu_time_ms=item["cpu_time_ms"],
                length=item["len"],
                data=item["data"],
            )
            for item in list(data.values())
        ]

    async def fetch_evse(self) -> list[EVSEData]:
        data = await self._fetch_data("evse")
        return [
            EVSEData(
                cb_id=item["cb_id"],
                connection_status=item["connection_status"],
                evse=[
                    EVSEInfo(
                        id=evse_item["id"],
                        state=evse_item["state"],
                        current=evse_item["current"],
                    )
                    for evse_item in item["evse"]
                ],
            )
            for item in list(data.values())
        ]
