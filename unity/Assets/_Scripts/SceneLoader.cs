using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// Fetches a previously-saved scene from the backend by session ID and builds
/// it in the scene using the attached SceneBuilder.
///
/// Setup:
///   1. Attach this script to the same GameObject as SceneBuilder (or any
///      active GameObject — then drag the SceneBuilder into the inspector slot).
///   2. Set Session Id in the Inspector to the UUID returned by /scene/generate.
///   3. The scene will load automatically on Start, or right-click the component
///      header and choose "Load Scene" to reload during Play Mode.
/// </summary>
public class SceneLoader : MonoBehaviour
{
    [SerializeField] private string apiBaseUrl = "http://127.0.0.1:8000/scene/load";
    [SerializeField] private string sessionId;
    [SerializeField] private SceneBuilder sceneBuilder;

    private void Start()
    {
        if (string.IsNullOrWhiteSpace(sessionId))
        {
            Debug.LogWarning("[SceneLoader] No Session Id set — skipping auto-load.");
            return;
        }
        StartCoroutine(LoadSceneCoroutine());
    }

    /// <summary>
    /// Re-trigger a load during Play Mode from the Inspector context menu.
    /// </summary>
    [ContextMenu("Load Scene")]
    public void LoadScene()
    {
        if (!Application.isPlaying)
        {
            Debug.LogWarning("[SceneLoader] 'Load Scene' only works in Play Mode.");
            return;
        }
        if (string.IsNullOrWhiteSpace(sessionId))
        {
            Debug.LogError("[SceneLoader] Session Id is empty.");
            return;
        }
        StartCoroutine(LoadSceneCoroutine());
    }

    private IEnumerator LoadSceneCoroutine()
    {
        string url = $"{apiBaseUrl}/{sessionId.Trim()}";
        Debug.Log($"[SceneLoader] GET {url}");

        using UnityWebRequest request = UnityWebRequest.Get(url);
        yield return request.SendWebRequest();

        if (request.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError($"[SceneLoader] Request failed ({request.responseCode}): {request.error}");
            yield break;
        }

        string json = request.downloadHandler.text;
        SceneResponseData response = JsonUtility.FromJson<SceneResponseData>(json);

        if (response?.objects == null)
        {
            Debug.LogError("[SceneLoader] Failed to parse scene response.");
            yield break;
        }

        if (sceneBuilder == null)
        {
            Debug.LogError("[SceneLoader] SceneBuilder reference is not set.");
            yield break;
        }

        sceneBuilder.BuildScene(response);
        Debug.Log($"[SceneLoader] Loaded session '{sessionId}' — {response.objects.Count} objects.");
    }
}
