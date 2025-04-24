from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


# NOTE(es3n1n): Do not forget to update `user_configs` table in the database
class UserConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stats_opt_out: Annotated[bool, Field(description='Opt out from stats')] = False
    add_media_button: Annotated[bool, Field(description='Add media button to message')] = True
    add_song_link: Annotated[bool, Field(description='Add song link url to message')] = True
    add_bitrate: Annotated[bool, Field(description='Add bitrate to message')] = False
    add_sample_rate: Annotated[bool, Field(description='Add sample rate to message')] = False
    lowercase_mode: Annotated[bool, Field(description='Everything in lowercase')] = False

    def text(self, text: str) -> str:
        if self.lowercase_mode:
            text = text.lower()
        return text
