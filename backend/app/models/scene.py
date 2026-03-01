from enum import Enum
from pydantic import BaseModel, Field


class PrimitiveType(str, Enum):
    cube = "cube"
    sphere = "sphere"
    cylinder = "cylinder"
    plane = "plane"
    capsule = "capsule"


class LightType(str, Enum):
    directional = "directional"
    point = "point"
    spot = "spot"


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


class LightObject(BaseModel):
    name: str
    light_type: LightType
    position: Vec3
    rotation: Vec3        # Euler angles; directional/spot lights use this for direction
    color: Color
    intensity: float      # directional: 1–2, point/spot: 0.5–5
    range: float          # point and spot only (units); ignored for directional
    spot_angle: float     # spot only (degrees, 1–179); ignored for other types


class SceneRequest(BaseModel):
    description: str


class SceneResponse(BaseModel):
    objects: list[SceneObject]
    lights: list[LightObject] = Field(default_factory=list)
