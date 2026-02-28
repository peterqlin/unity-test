using System.Collections;
using UnityEngine;
using UnityEngine.Networking; // Required for web requests

public class LocalAPIHandler : MonoBehaviour
{
    // The address of your local API
    private string url = "http://127.0.0.1:8000/";

    void Start()
    {
        // We "Start" the Coroutine here. 
        // Web requests cannot be "instant" functions; they must wait for the server.
        StartCoroutine(GetRequest(url));
    }

    IEnumerator GetRequest(string uri)
    {
        using (UnityWebRequest webRequest = UnityWebRequest.Get(uri))
        {
            // This line tells Unity to wait here until the network responds
            yield return webRequest.SendWebRequest();

            // Check if there were any errors
            if (webRequest.result == UnityWebRequest.Result.ConnectionError || 
                webRequest.result == UnityWebRequest.Result.ProtocolError)
            {
                Debug.LogError("Error: " + webRequest.error);
            }
            else
            {
                // If successful, print the "downloadHandler.text" to the Console
                Debug.Log("API Response: " + webRequest.downloadHandler.text);
            }
        }
    }
}
