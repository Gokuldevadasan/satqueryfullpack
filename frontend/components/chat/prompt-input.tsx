"use client";

import { ArrowUp, ImagePlus, LoaderCircle, X } from "lucide-react";
import { type FormEvent, useRef } from "react";
import { LiquidGlass } from "@/components/ui/liquid-glass";
import type { ImageAttachment } from "@/types/chat";

type Props = {
  onSubmit: () => void;
  onAddImages: (files: FileList) => void;
  onRemoveImage: (index: number) => void;
  images: ImageAttachment[];
  loading: boolean;
};

export function PromptInput({ onSubmit, onAddImages, onRemoveImage, images, loading }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <LiquidGlass className="rounded-[22px] p-3 transition-all duration-300 hover:border-white/[0.16] hover:bg-white/[0.06] focus-within:border-blue-400/30 focus-within:shadow-[0_20px_80px_rgba(0,0,0,0.5),0_0_40px_rgba(10,132,255,0.08)]">
      {images.length > 0 && (
        <div className="mb-3 flex gap-2 overflow-x-auto pb-1">
          {images.map((image, index) => (
            <div key={`${image.file.name}-${index}`} className="group relative size-14 shrink-0 overflow-hidden rounded-xl border border-white/10 bg-white/[.06]">
              {image.preview ? <img src={image.preview} alt={image.file.name} className="size-full object-cover" /> : <ImagePlus className="m-[18px] text-white/50" size={20} />}
              <button type="button" onClick={() => onRemoveImage(index)} disabled={loading} aria-label={`Remove ${image.file.name}`} className="absolute right-1 top-1 grid size-5 place-items-center rounded-full bg-black/70 text-white opacity-0 transition group-hover:opacity-100 focus:opacity-100">
                <X size={11} />
              </button>
            </div>
          ))}
        </div>
      )}
      <form onSubmit={submit} className="flex items-center gap-3">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/tiff,.tif,.tiff"
          multiple
          className="sr-only"
          onChange={(event) => {
            if (event.target.files) onAddImages(event.target.files);
            event.currentTarget.value = "";
          }}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          aria-label="Add satellite images"
          className="focus-ring grid size-10 shrink-0 place-items-center rounded-full bg-white/[0.07] text-white/70 transition hover:bg-white/[0.12] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ImagePlus size={19} />
        </button>
        <p className="flex-1 text-sm text-white/55">
          {images.length ? `${images.length} image${images.length === 1 ? "" : "s"} ready for analysis` : "Upload satellite imagery for analysis"}
        </p>
        <button
          type="submit"
          disabled={loading || !images.length}
          aria-label="Analyze imagery"
          className="focus-ring grid size-10 shrink-0 place-items-center rounded-full bg-[#0A84FF] text-white transition-all duration-200 hover:scale-[1.04] hover:bg-[#2997FF] active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? <LoaderCircle size={17} className="animate-spin" /> : <ArrowUp size={18} strokeWidth={2.5} />}
        </button>
      </form>
    </LiquidGlass>
  );
}
