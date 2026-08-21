// Runs the optional semantic pass away from the page's main thread.
// The worker owns the model and its ONNX/WASM work; the UI only receives
// progress and the final finding list.
import { analyzeEmbeddings, onModelProgress } from "./embedding-analysis.js";

onModelProgress((event) => {
  self.postMessage({ type: "progress", event });
});

self.onmessage = async (message) => {
  const { id, text, lang } = message.data || {};
  if (!id) return;
  try {
    const result = await analyzeEmbeddings(text, lang || "es");
    self.postMessage({ type: "result", id, result });
  } catch (error) {
    self.postMessage({
      type: "error",
      id,
      error: error instanceof Error ? error.message : String(error),
    });
  }
};
