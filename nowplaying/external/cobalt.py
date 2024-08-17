from dataclasses import dataclass
from secrets import choice
from typing import TypedDict

import orjson
from httpx import AsyncClient, HTTPError, Timeout

from nowplaying.bot.reporter import report_error
from nowplaying.util.http import STATUS_OK
from nowplaying.util.logger import logger


class CobaltAPIInstance(TypedDict):
    api_online: bool
    cors: int
    frontend_online: bool
    commit: str
    services: dict[str, bool]
    version: str
    branch: str
    score: int
    protocol: str
    name: str
    api: str


InstancesResponse = list[CobaltAPIInstance]


@dataclass(frozen=True)
class CobaltInstance:
    proto: str
    address: str

    @classmethod
    def default(cls) -> 'CobaltInstance':
        return cls(
            proto='https',
            address='api.cobalt.tools',
        )

    @property
    def url(self) -> str:
        return f'{self.proto}://{self.address}'


def get_client() -> AsyncClient:
    return AsyncClient(
        headers={
            'Accept': 'application/json',
            'User-Agent': 'playinnow/1.0',
        },
        timeout=Timeout(timeout=2),
    )


class Cobalt:
    def __init__(self) -> None:
        self.instance: CobaltInstance = CobaltInstance.default()
        self.banned_instances: list[str] = []

    async def re_roll_instance(self, *, ban_current: bool = False) -> None:
        if ban_current:
            self.banned_instances.append(self.instance.address)

        try:
            async with get_client() as client:
                instances_request = await client.get('https://instances.hyper.lol/instances.json')
            instances_request.raise_for_status()

            instances_data: InstancesResponse = orjson.loads(instances_request.content)
        except (HTTPError, orjson.JSONDecodeError):
            # In case we want to reset an instance because the current one is dead,
            #   lets fallback to the default one
            self._reset_instance()
            return

        # Let's filter out instances with low score and without YouTube support
        instances_data = [
            inst
            for inst in instances_data
            if (
                inst.get('score', 0) == 100  # noqa: PLR2004
                and inst.get('services', {}).get('youtube', False)
                and inst.get('api_online')
            )
        ]

        # No available instances
        if not instances_data:
            self._reset_instance()
            return

        # Get a new random available instance
        instance_json: CobaltAPIInstance | None = None
        while not instance_json or instance_json['api'] in {*self.banned_instances, self.instance.address}:
            instance_json = choice(instances_data)

        self.instance = CobaltInstance(
            proto=instance_json['protocol'],
            address=instance_json['api'],
        )
        logger.info(f'Re-rolled instance to {self.instance.url}')

    async def get_mp3_stream_url(self, youtube_url: str) -> str | None:
        try:
            async with get_client() as client:
                json_response = await client.post(
                    f'{self.instance.url}/api/json',
                    json={
                        'isAudioOnly': 'true',
                        'url': youtube_url,
                        'aFormat': 'mp3',
                    },
                )
        except HTTPError:
            return None

        if json_response.status_code != STATUS_OK:
            await report_error(f'Got a weird response from {self.instance.url}: {json_response.text}')
            return None

        try:
            json_data = orjson.loads(json_response.content)
        except orjson.JSONDecodeError:
            await report_error(f'Got unsupported json from {self.instance.url}: {json_response.text}')
            return None

        status: str = json_data.get('status', 'error')
        url: str | None = json_data.get('url', None)
        if status in {'error', 'rate-limit'} or url is None:
            await report_error(f'Got an error/ratelimit from {self.instance.url}: {json_response.text}')
            return None

        return url

    def _reset_instance(self) -> None:
        self.instance = CobaltInstance.default()
