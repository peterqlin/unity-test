using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// POSTs a scene description to the backend, then spawns Unity primitives
/// matching the returned scene JSON. All generated objects are parented to
/// a root transform so they can be cleared cleanly on re-generation.
///
/// Setup:
///   1. Attach to an empty GameObject in the scene.
///   2. Assign a child empty GameObject to "Scene Root" in the Inspector
///      (or leave blank — one will be created automatically).
///   3. Make sure tags "Ground", "Obstacle", "Collectible" exist in
///      Edit > Project Settings > Tags and Layers (already added via TagManager.asset).
///   4. Start the backend before entering Play Mode.
/// </summary>
public class SceneBuilder : MonoBehaviour
{
    [SerializeField] private string apiUrl = "http://127.0.0.1:8000/scene/generate";
    [SerializeField] private string sceneDescription = "a simple arena with red cube obstacles and gold sphere collectibles";
    [SerializeField] private Transform sceneRoot;

    private void Awake()
    {
        // Create the scene root early so it exists in the hierarchy from the
        // moment Play Mode starts, rather than only after the web request returns.
        EnsureSceneRoot();
    }

    private void Start() { }

    // Right-click the component header in the Inspector and choose
    // "Generate Scene" to re-trigger during Play Mode without restarting.
    [ContextMenu("Generate Scene")]
    public void GenerateScene()
    {
        if (!Application.isPlaying)
        {
            Debug.LogWarning("[SceneBuilder] 'Generate Scene' only works in Play Mode (StartCoroutine requires an active MonoBehaviour).");
            return;
        }
        GenerateScene(sceneDescription);
    }

    public void GenerateScene(string description)
    {
        StartCoroutine(GenerateSceneCoroutine(description));
    }

    private IEnumerator GenerateSceneCoroutine(string description)
    {
        string requestBody = JsonUtility.ToJson(new SceneRequestData { description = description });

        using UnityWebRequest request = new UnityWebRequest(apiUrl, "POST");
        request.uploadHandler = new UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(requestBody));
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError($"[SceneBuilder] Request failed: {request.error}");
            yield break;
        }

        SceneResponseData response = JsonUtility.FromJson<SceneResponseData>(request.downloadHandler.text);
        if (response?.objects == null)
        {
            Debug.LogError("[SceneBuilder] Failed to parse scene response.");
            yield break;
        }

        BuildScene(response);
    }

    private void BuildScene(SceneResponseData response)
    {
        EnsureSceneRoot();
        ClearScene();

        foreach (SceneObjectData obj in response.objects)
        {
            GameObject go = CreatePrimitive(obj.type);
            if (go == null) continue;

            go.name = obj.name;
            go.transform.SetParent(sceneRoot, worldPositionStays: false);
            go.transform.localPosition = obj.position.ToVector3();
            go.transform.localEulerAngles = obj.rotation.ToVector3();
            go.transform.localScale = obj.scale.ToVector3();

            ApplyColor(go, obj.color.ToColor());
            ConfigureCollider(go, obj.has_collider, obj.is_trigger);
            ApplyTag(go, obj.tag);
        }

        Debug.Log($"[SceneBuilder] Built scene with {response.objects.Count} objects.");
    }

    private void EnsureSceneRoot()
    {
        if (sceneRoot != null) return;
        sceneRoot = new GameObject("GeneratedScene").transform;
    }

    private void ClearScene()
    {
        for (int i = sceneRoot.childCount - 1; i >= 0; i--)
            Destroy(sceneRoot.GetChild(i).gameObject);
    }

    private static GameObject CreatePrimitive(string type)
    {
        switch (type)
        {
            case "cube":     return GameObject.CreatePrimitive(PrimitiveType.Cube);
            case "sphere":   return GameObject.CreatePrimitive(PrimitiveType.Sphere);
            case "cylinder": return GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            case "plane":    return GameObject.CreatePrimitive(PrimitiveType.Plane);
            case "capsule":  return GameObject.CreatePrimitive(PrimitiveType.Capsule);
            default:
                Debug.LogWarning($"[SceneBuilder] Unknown primitive type: '{type}'");
                return null;
        }
    }

    // Sets color on URP/Lit primitives. Handles both _BaseColor (URP) and
    // _Color (Built-in RP) so the script is render-pipeline-agnostic.
    private static void ApplyColor(GameObject go, Color color)
    {
        Renderer rend = go.GetComponent<Renderer>();
        if (rend == null) return;

        // renderer.material creates a per-object material instance automatically
        Material mat = rend.material;
        if (mat.HasProperty("_BaseColor"))
            mat.SetColor("_BaseColor", color);
        if (mat.HasProperty("_Color"))
            mat.SetColor("_Color", color);
    }

    private static void ConfigureCollider(GameObject go, bool hasCollider, bool isTrigger)
    {
        Collider col = go.GetComponent<Collider>();
        if (col == null) return;

        if (!hasCollider)
        {
            Destroy(col);
            return;
        }

        col.isTrigger = isTrigger;
    }

    private static void ApplyTag(GameObject go, string tag)
    {
        if (string.IsNullOrEmpty(tag)) return;
        try
        {
            go.tag = tag;
        }
        catch
        {
            Debug.LogWarning($"[SceneBuilder] Tag '{tag}' is not defined. Add it in Edit > Project Settings > Tags and Layers.");
        }
    }
}
