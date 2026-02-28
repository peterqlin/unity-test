from fastapi import APIRouter
from app.models.scene import Color, PrimitiveType, SceneObject, SceneRequest, SceneResponse, Vec3

router = APIRouter(prefix="/scene", tags=["scene"])

# Mock scene: a flat arena with obstacles, pillars, and collectibles.
# Replace this with a real LLM call once the schema is validated in Unity.
MOCK_SCENE = SceneResponse(
    objects=[
        # Ground
        SceneObject(
            name="Ground",
            type=PrimitiveType.plane,
            position=Vec3(x=0, y=0, z=0),
            rotation=Vec3(x=0, y=0, z=0),
            scale=Vec3(x=5, y=1, z=5),
            color=Color(r=0.55, g=0.55, b=0.55),
            has_collider=True,
            is_trigger=False,
            tag="Ground",
        ),
        # Obstacles
        SceneObject(
            name="Obstacle_1",
            type=PrimitiveType.cube,
            position=Vec3(x=2, y=0.5, z=0),
            rotation=Vec3(x=0, y=30, z=0),
            scale=Vec3(x=1, y=1, z=1),
            color=Color(r=0.8, g=0.2, b=0.2),
            has_collider=True,
            is_trigger=False,
            tag="Obstacle",
        ),
        SceneObject(
            name="Obstacle_2",
            type=PrimitiveType.cube,
            position=Vec3(x=-2, y=0.5, z=3),
            rotation=Vec3(x=0, y=0, z=0),
            scale=Vec3(x=1, y=1, z=1),
            color=Color(r=0.8, g=0.2, b=0.2),
            has_collider=True,
            is_trigger=False,
            tag="Obstacle",
        ),
        SceneObject(
            name="Obstacle_3",
            type=PrimitiveType.cube,
            position=Vec3(x=0, y=0.5, z=-4),
            rotation=Vec3(x=0, y=0, z=0),
            scale=Vec3(x=2, y=1, z=2),
            color=Color(r=0.6, g=0.1, b=0.1),
            has_collider=True,
            is_trigger=False,
            tag="Obstacle",
        ),
        # Pillars
        SceneObject(
            name="Pillar_1",
            type=PrimitiveType.cylinder,
            position=Vec3(x=4, y=1, z=4),
            rotation=Vec3(x=0, y=0, z=0),
            scale=Vec3(x=0.5, y=2, z=0.5),
            color=Color(r=0.2, g=0.4, b=0.8),
            has_collider=True,
            is_trigger=False,
            tag="Obstacle",
        ),
        SceneObject(
            name="Pillar_2",
            type=PrimitiveType.cylinder,
            position=Vec3(x=-4, y=1, z=4),
            rotation=Vec3(x=0, y=0, z=0),
            scale=Vec3(x=0.5, y=2, z=0.5),
            color=Color(r=0.2, g=0.4, b=0.8),
            has_collider=True,
            is_trigger=False,
            tag="Obstacle",
        ),
        # Collectibles
        SceneObject(
            name="Collectible_1",
            type=PrimitiveType.sphere,
            position=Vec3(x=0, y=0.5, z=4),
            rotation=Vec3(x=0, y=0, z=0),
            scale=Vec3(x=0.5, y=0.5, z=0.5),
            color=Color(r=1.0, g=0.85, b=0.0),
            has_collider=True,
            is_trigger=True,
            tag="Collectible",
        ),
        SceneObject(
            name="Collectible_2",
            type=PrimitiveType.sphere,
            position=Vec3(x=3, y=0.5, z=-3),
            rotation=Vec3(x=0, y=0, z=0),
            scale=Vec3(x=0.5, y=0.5, z=0.5),
            color=Color(r=1.0, g=0.85, b=0.0),
            has_collider=True,
            is_trigger=True,
            tag="Collectible",
        ),
    ]
)


@router.post("/generate", response_model=SceneResponse)
def generate_scene(request: SceneRequest) -> SceneResponse:
    """
    Accepts a plain-text scene description from Unity and returns a structured
    scene JSON. Currently returns a hardcoded mock; will be replaced with a
    real LLM call once the schema is validated end-to-end.
    """
    return MOCK_SCENE
