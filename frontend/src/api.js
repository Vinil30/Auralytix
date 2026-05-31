import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  headers: {
    "Content-Type": "application/json"
  }
});

export async function extractContent(videoAUrl, videoBUrl) {
  const response = await api.post("/extract", {
    video_a_url: videoAUrl,
    video_b_url: videoBUrl
  });

  return response.data;
}

export async function sendMessageStream(sessionId, query, handlers = {}) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || "";
  const response = await fetch(`${baseURL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      session_id: sessionId,
      query
    })
  });

  if (!response.ok || !response.body) {
    throw new Error("Unable to stream response.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const event of events) {
      const lines = event.split("\n");
      const eventType = lines.find(line => line.startsWith("event: "))?.slice(7);
      const data = lines.find(line => line.startsWith("data: "))?.slice(6) || "";

      if (eventType === "citations") {
        handlers.onCitations?.(JSON.parse(data));
      } else if (eventType === "done") {
        handlers.onDone?.();
      } else if (data) {
        let token = data;

        try {
          token = JSON.parse(data);
        } catch {
          token = data;
        }

        handlers.onToken?.(token);
      }
    }
  }
}
