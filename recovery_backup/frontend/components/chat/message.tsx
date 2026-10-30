"use client";

import { Bot, UserRound } from "lucide-react";
import { motion } from "motion/react";
import type { AnalysisResponse, Message as MessageType } from "@/types/chat";

function displayNumber(value: number | null, digits = 1, suffix = "") {
  return value === null ? "Unavailable" : `${value.toFixed(digits)}${suffix}`;
}

function Dashboard({ analysis }: { analysis: AnalysisResponse }) {
  return (
    <div className="mt-3 space-y-4">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[.18em] text-[#0A84FF]">
          SatQuery {analysis.satquery_version}
        </p>
        <h3 className="mt-1 text-base font-medium text-white">{analysis.input.filename}</h3>
        <p className="text-xs text-[#86868B]">
          {analysis.input.type} · {analysis.input.bands} bands · {analysis.input.width} × {analysis.input.height}
        </p>
        <p className="text-xs text-white/45">Analysis status: {analysis.status}</p>
      </header>
      {analysis.message && <p className="text-xs text-amber-200">{analysis.message}</p>}
      <div className="grid gap-3 sm:grid-cols-2">
        <section className="rounded-xl border border-white/[.08] bg-black/10 p-3">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-white/60">Terrain</h4>
          <p className="text-lg font-medium text-white">{analysis.terrain.class ?? "Unavailable"}</p>
          {analysis.terrain.reason && <p className="text-xs text-white/55">{analysis.terrain.reason}</p>}
          <p className="text-xs text-white/60">
            Confidence: {displayNumber(analysis.terrain.confidence === null ? null : analysis.terrain.confidence * 100, 1, "%")}
          </p>
          {analysis.terrain.top_predictions.length > 0 && (
            <ul className="mt-2 space-y-1 text-xs text-white/70">
              {analysis.terrain.top_predictions.map((prediction) => (
                <li key={prediction.class} className="flex justify-between gap-3">
                  <span>{prediction.class}</span>
                  <span>{displayNumber(prediction.confidence * 100, 1, "%")}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section className="rounded-xl border border-white/[.08] bg-black/10 p-3">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-white/60">Location & weather</h4>
          <p>Place: {analysis.location.place ?? "Unknown"}</p>
          <p>Latitude: {displayNumber(analysis.location.latitude, 5)}</p>
          <p>Longitude: {displayNumber(analysis.location.longitude, 5)}</p>
          <p>Air temperature: {displayNumber(analysis.weather.temperature_c, 1, " °C")}</p>
          <p>Feels like: {displayNumber(analysis.weather.feels_like_c, 1, " °C")}</p>
          <p>Humidity: {displayNumber(analysis.weather.humidity_percent, 0, "%")}</p>
          <p>Wind: {displayNumber(analysis.weather.wind_kmh, 1, " km/h")}</p>
          <p>Condition: {analysis.weather.weather_description ?? analysis.weather.condition ?? "Unavailable"}</p>
          <p>CRS: {analysis.gis.crs ?? "Unavailable"}</p>
          <p>Pixel size: {analysis.gis.pixel_size ? analysis.gis.pixel_size.map((size) => `${size.toFixed(2)}`).join(" × ") : "Unavailable"}</p>
          {!analysis.weather.available && <p className="mt-1 text-xs text-white/45">{analysis.weather.note}</p>}
          {analysis.location.location_reason && <p className="mt-1 text-xs text-white/45">{analysis.location.location_reason}</p>}
        </section>
        <section className="rounded-xl border border-white/[.08] bg-black/10 p-3">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-white/60">Spectral analysis</h4>
          {Object.entries(analysis.spectral).map(([name, index]) => <p key={name}>{name.toUpperCase()}: {index.available ? displayNumber(index.statistics?.mean ?? null, 3) : index.reason}</p>)}
        </section>
      </div>
      <p className="text-xs text-white/50">
        Model: {analysis.model.used ? analysis.model.name : `Not used — ${analysis.model.reason ?? "no compatible model"}`} · Backend: SatQuery Medium · Input: {analysis.input.band_details?.length ? `Sentinel-2 ${analysis.input.band_details.map((band) => band.id).join(", ")}` : analysis.input.type}
      </p>
      {analysis.gis.note && <p className="text-xs text-white/45">{analysis.gis.note}</p>}
      <details className="rounded-lg border border-white/[.08] px-3 py-2">
        <summary className="cursor-pointer text-xs text-white/60">View complete JSON response</summary>
        <pre className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap break-words text-[11px] leading-5 text-white/60">
          {JSON.stringify(analysis, null, 2)}
        </pre>
      </details>
    </div>
  );
}

export function Message({ message }: { message: MessageType }) {
  const user = message.role === "user";
  return (
    <motion.article
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-3 ${user ? "justify-end" : "justify-start"}`}
    >
      {!user && <div className="mt-1 grid size-7 shrink-0 place-items-center rounded-full bg-[#0A84FF] text-white"><Bot size={15} /></div>}
      <div className={`max-w-[92%] rounded-2xl px-4 py-3 text-sm leading-6 sm:max-w-[88%] ${user ? "bg-white/[.09] text-[#F5F5F7]" : "border border-white/[.08] bg-white/[.035] text-[#d4d4d7]"}`}>
        {message.images && <div className="mb-3 grid grid-cols-2 gap-2">{message.images.map((image, index) => image.preview && <img key={`${image.file.name}-${index}`} src={image.preview} alt={image.file.name} className="aspect-[1.4] rounded-lg object-cover" />)}</div>}
        <p className="whitespace-pre-wrap">{message.content}</p>
        {message.analyses?.map((analysis, index) => <Dashboard key={`${analysis.input.filename}-${index}`} analysis={analysis} />)}
      </div>
      {user && <div className="mt-1 grid size-7 shrink-0 place-items-center rounded-full bg-white/[.1] text-[#F5F5F7]"><UserRound size={14} /></div>}
    </motion.article>
  );
}
