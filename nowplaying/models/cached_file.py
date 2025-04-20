import orjson
from pydantic import BaseModel, field_validator

from nowplaying.external.udownloader import SongQualityInfo


class CachedFile(BaseModel):
    file_id: str
    cached_by_user_id: int | None
    quality_info: SongQualityInfo

    @field_validator('quality_info', mode='before')
    @classmethod
    def parse_quality_info(cls, value: str | SongQualityInfo) -> SongQualityInfo:
        if isinstance(value, str):
            try:
                return orjson.loads(value)
            except orjson.JSONDecodeError as e:
                err_msg = f'Invalid JSON for quality_info: {e}'
                raise ValueError(err_msg) from e
        return value
