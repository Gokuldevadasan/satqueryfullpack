export type ImageAttachment = { file: File; preview?: string };

export type Prediction = { class: string; confidence: number };

export type AnalysisResponse = {
  satquery_version: string;
  status: string;
  message: string | null;
  input: {
    filename: string;
    type: string;
    bands: number;
    width: number;
    height: number;
    band_names?: string[];
    georeferenced?: boolean;
    nodata?: number | null;
    band_details?: { id: string; name: string; resolution_m: number; sensor: string }[];
  };
  terrain: {
    class: string | null;
    confidence: number | null;
    top_predictions: Prediction[];
    available?: boolean;
    reason?: string | null;
  };
  location: {
    latitude: number | null;
    longitude: number | null;
    place: string | null;
    source: string;
    location_status?: string;
    location_reason?: string | null;
  };
  gis: {
    crs: string | null;
    pixel_size: number[] | null;
    bounds: number[] | null;
    note: string | null;
  };
  water: {
    detected: boolean | null;
    coverage_percent: number | null;
    area_m2: number | null;
    area_km2: number | null;
    depth: string;
    volume: string;
  };
  vegetation: { coverage_percent: number | null; ndvi: number | null; method?: string; reason?: string | null };
  built_up: { coverage_percent: number | null; ndbi: number | null; method?: string; reason?: string | null };
  spectral: Record<string, { available: boolean; reason: string | null; statistics: { mean: number | null; min: number | null; max: number | null; median: number | null; valid_pixel_count: number } | null; threshold: number | null; coverage_percent: number | null }>;
  weather: {
    available: boolean;
    temperature_c: number | null;
    feels_like_c: number | null;
    humidity_percent: number | null;
    wind_kmh: number | null;
    condition: string | number | null;
    note: string;
    error?: string;
    weather_description?: string | null;
  };
  model: {
    name: string | null;
    type: string | null;
    parameters?: number | null;
    backend: string | null;
    path: string | null;
    status: string;
    message?: string;
    used?: boolean;
    reason?: string | null;
  };
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  images?: ImageAttachment[];
  analyses?: AnalysisResponse[];
  createdAt: number;
};
