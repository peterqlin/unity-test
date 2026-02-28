using System;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// C# mirror of the backend's scene JSON schema.
/// All classes must be [Serializable] for JsonUtility to work.
/// </summary>

[Serializable]
public class Vec3Data
{
    public float x, y, z;
    public Vector3 ToVector3() => new Vector3(x, y, z);
}

[Serializable]
public class ColorData
{
    public float r, g, b;
    public Color ToColor() => new Color(r, g, b);
}

[Serializable]
public class SceneObjectData
{
    public string name;
    public string type;       // "cube" | "sphere" | "cylinder" | "plane" | "capsule"
    public Vec3Data position;
    public Vec3Data rotation; // Euler angles in degrees
    public Vec3Data scale;
    public ColorData color;   // Normalized 0–1 floats
    public bool has_collider;
    public bool is_trigger;
    public string tag;
}

[Serializable]
public class SceneResponseData
{
    public List<SceneObjectData> objects;
}

// Sent to POST /scene/generate
[Serializable]
public class SceneRequestData
{
    public string description;
}
