from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


# NOTE(es3n1n): Do not forget to update `user_configs` table in the database
class UserConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stats_opt_out: Annotated[bool, Field(description='Opt out from stats')] = False
