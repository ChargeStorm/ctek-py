import socket

import aiohttp


class NanogridAir:
    def __init__(self, device_ip: str | None = None) -> None:
        self.device_ip = device_ip
        self._initialized = False

    @staticmethod
    async def get_ip(hostname="ctek-ng-air.local") -> str | None:
        try:
            ip = socket.gethostbyname(hostname)
            if ip:
                return ip
        except socket.gaierror:
            return None

        return None

    async def _initialize(self):
        if not self._initialized:
            if not self.device_ip:
                self.device_ip = await self.get_ip()
            self._initialized = True

    async def _fetch_data(self, endpoint: str) -> dict:
        await self._initialize()
        url = f"http://{self.device_ip}/{endpoint}/"
        async with aiohttp.ClientSession() as session, session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def fetch_mac(self) -> str:
        data = await self._fetch_data("status")
        return data["deviceInfo"]["mac"]

    async def fetch_meter_data(self) -> dict:
        return await self._fetch_data("meter")

    async def fetch_meterraw(self) -> dict:
        return await self._fetch_data("meterraw")

    async def fetch_evse(self) -> dict:
        return await self._fetch_data("evse")
