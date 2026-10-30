"use client";

import { ImagePlus, X } from "lucide-react";
import { motion } from "motion/react";
import type { ImageAttachment } from "@/types/chat";

type Props = { images: ImageAttachment[]; onAdd: (files: FileList | File[]) => void; onRemove: (index: number) => void; disabled?: boolean };
export function ImageUpload({ images, onAdd, onRemove, disabled }: Props) {
  return <div className="space-y-3">
    {images.length > 0 && <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">{images.map((image, index) => <motion.div initial={{ opacity: 0, scale: .96 }} animate={{ opacity: 1, scale: 1 }} key={`${image.file.name}-${index}`} className="liquid-glass group relative aspect-[1.5] rounded-xl border-white/[.14]">
      {image.preview ? <img src={image.preview} alt={image.file.name} className="size-full object-cover" /> : <div className="grid size-full place-items-center p-3 text-center text-xs text-[#86868B]"><ImagePlus size={18} /><span className="mt-1 truncate max-w-full">{image.file.name}</span></div>}
      <button type="button" aria-label={`Remove ${image.file.name}`} onClick={() => onRemove(index)} disabled={disabled} className="focus-ring absolute right-2 top-2 grid size-7 place-items-center rounded-full bg-black/70 text-white opacity-100 transition hover:bg-red-500 disabled:opacity-40 sm:opacity-0 sm:group-hover:opacity-100"><X size={14} /></button>
      <span className="absolute inset-x-0 bottom-0 truncate bg-gradient-to-t from-black/80 to-transparent px-2 pb-1.5 pt-6 text-[10px] text-white/80">{image.file.name}</span>
    </motion.div>)}</div>}
    <label className={`focus-within:ring-2 focus-within:ring-[#0A84FF] flex min-h-28 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed transition ${disabled ? "cursor-not-allowed border-white/5 opacity-50" : "border-white/[.18] bg-white/[.025] hover:border-[#0A84FF]/70 hover:bg-[#0A84FF]/[.04]"}`} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); if (!disabled) onAdd(event.dataTransfer.files); }}>
      <ImagePlus className="mb-2 text-[#0A84FF]" size={22} /><span className="text-sm text-[#F5F5F7]">Upload satellite imagery</span><span className="mt-1 text-xs text-[#86868B]">Drop PNG, JPEG, TIFF, or GeoTIFF files here</span><input className="sr-only" type="file" accept="image/png,image/jpeg,image/tiff,.tif,.tiff" multiple disabled={disabled} onChange={(event) => { if (event.target.files) onAdd(event.target.files); event.currentTarget.value = ""; }} />
    </label>
  </div>;
}
