from enum import Enum
from pydantic import BaseModel, Field


class PrimitiveType(str, Enum):
    cube = "cube"
    sphere = "sphere"
    cylinder = "cylinder"
    plane = "plane"
    capsule = "capsule"


class Vec3(BaseModel):
    x: float
    y: float
    z: float


class Color(BaseModel):
    r: float = Field(ge=0.0, le=1.0)
    g: float = Field(ge=0.0, le=1.0)
    b: float = Field(ge=0.0, le=1.0)


class SceneObject(BaseModel):
    name: str
    type: PrimitiveType
    position: Vec3
    rotation: Vec3
    scale: Vec3
    color: Color
    has_collider: bool = True
    is_trigger: bool = False
    tag: str = "Untagged"


class SceneRequest(BaseModel):
    description: str


class SceneResponse(BaseModel):
    objects: list[SceneObject]
