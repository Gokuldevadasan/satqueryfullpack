import type { AnalysisResponse } from "@/types/chat";

const backendUrl =
  process.env.NEXT_PUBLIC_BACKEND_URL?.trim().replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

function isAnalysisResponse(value: unknown): value is AnalysisResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "satquery_version" in value &&
    "input" in value &&
    "terrain" in value &&
    "location" in value &&
    "gis" in value &&
    "water" in value &&
    "vegetation" in value &&
    "built_up" in value &&
    "spectral" in value &&
    "weather" in value &&
    "model" in value
  );
}

export async function analyzeSatelliteImages(images: File[]): Promise<AnalysisResponse[]> {
  return Promise.all(
    images.map(async (image) => {
      const formData = new FormData();
      formData.append("image", image);
      let response: Response;
      try {
        response = await fetch(`${backendUrl}/analyze`, {
          method: "POST",
          body: formData,
        });
      } catch {
        throw new Error("BACKEND_UNAVAILABLE");
      }
      if (!response.ok) throw new Error("ANALYSIS_FAILED");
      const data: unknown = await response.json();
      if (!isAnalysisResponse(data)) throw new Error("ANALYSIS_FAILED");
      return data;
    }),
  );
}
