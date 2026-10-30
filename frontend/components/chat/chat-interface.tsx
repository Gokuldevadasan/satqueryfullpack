"use client";

import { AlertCircle } from "lucide-react";
import { AnimatePresence, motion, useScroll, useTransform } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { analyzeSatelliteImages } from "@/lib/api";
import type { ImageAttachment, Message } from "@/types/chat";
import { Message as MessageItem } from "./message";
import { PromptInput } from "./prompt-input";

const supportedExtensions = ["png", "jpg", "jpeg", "tif", "tiff"];
function readableError(code: string) { return ({ NO_IMAGE: "Add at least one satellite image before analysis.", UNSUPPORTED_IMAGE: "Use PNG, JPEG, TIFF, or GeoTIFF image files.", BACKEND_UNAVAILABLE: "SatQuery is unavailable right now. Check that the backend is running and try again.", ANALYSIS_FAILED: "We couldn’t analyze those images. Please try again." } as Record<string, string>)[code] ?? "Something went wrong. Please try again."; }

export function ChatInterface() {
  const [images, setImages] = useState<ImageAttachment[]>([]); const [messages, setMessages] = useState<Message[]>([]); const [loading, setLoading] = useState(false); const [error, setError] = useState<string | null>(null);
  const imagesRef = useRef(images);
  const chatRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: chatRef, offset: ["start end", "center center"] });
  const bloom = useTransform(scrollYProgress, [0, .8, 1], ["0 16px 50px rgba(0,0,0,.42), 0 0 0 rgba(10,132,255,0)", "0 24px 85px rgba(0,0,0,.52), 0 0 52px rgba(10,132,255,.16)", "0 20px 70px rgba(0,0,0,.48), 0 0 24px rgba(10,132,255,.08)"]);
  const bloomScale = useTransform(scrollYProgress, [0, .8, 1], [.975, 1, .99]);
  useEffect(() => { imagesRef.current = images; }, [images]);
  useEffect(() => () => imagesRef.current.forEach((image) => image.preview && URL.revokeObjectURL(image.preview)), []);
  const addImages = (incoming: FileList | File[]) => { const files = Array.from(incoming); if (files.some((file) => !supportedExtensions.includes(file.name.split(".").pop()?.toLowerCase() ?? ""))) { setError(readableError("UNSUPPORTED_IMAGE")); return; } setError(null); setImages((current) => [...current, ...files.map((file) => ({ file, preview: file.type === "image/tiff" || /\.tiff?$/i.test(file.name) ? undefined : URL.createObjectURL(file) }))]); };
  const removeImage = (index: number) => setImages((current) => { const image = current[index]; if (image.preview) URL.revokeObjectURL(image.preview); return current.filter((_, itemIndex) => itemIndex !== index); });
  const submit = async () => { if (!images.length) return setError(readableError("NO_IMAGE")); setError(null); const userMessage: Message = { id: crypto.randomUUID(), role: "user", content: `Analyze ${images.length} image${images.length === 1 ? "" : "s"}.`, images: images.map((image) => ({ ...image })), createdAt: Date.now() }; setMessages((current) => [...current, userMessage]); setLoading(true); try { const analyses = await analyzeSatelliteImages(images.map((image) => image.file)); setMessages((current) => [...current, { id: crypto.randomUUID(), role: "assistant", content: "SatQuery Medium analysis", analyses, createdAt: Date.now() }]); } catch (caught) { setError(readableError(caught instanceof Error ? caught.message : "ANALYSIS_FAILED")); } finally { setLoading(false); } };
  return <section id="about" ref={chatRef} className="scroll-mt-8 py-10 sm:py-16"><div className="space-y-5"><AnimatePresence>{error && <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} role="alert" className="flex gap-2 rounded-xl border border-red-400/20 bg-red-400/[.07] px-3 py-2.5 text-sm text-red-200"><AlertCircle className="mt-0.5 shrink-0" size={16} />{error}</motion.div>}</AnimatePresence>
      {messages.length > 0 && <div className="space-y-5 border-t border-white/[.08] pt-5">{messages.map((message) => <MessageItem key={message.id} message={message} />)}{loading && <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 text-sm text-[#86868B]"><span className="flex gap-1"><i className="size-1.5 animate-bounce rounded-full bg-[#0A84FF] [animation-delay:-.2s]" /><i className="size-1.5 animate-bounce rounded-full bg-[#0A84FF] [animation-delay:-.1s]" /><i className="size-1.5 animate-bounce rounded-full bg-[#0A84FF]" /></span>Analyzing imagery...</motion.div>}</div>}
      <motion.div style={{ boxShadow: bloom, scale: bloomScale }}><PromptInput onSubmit={submit} onAddImages={addImages} onRemoveImage={removeImage} images={images} loading={loading} /></motion.div>
    </div></section>;
}
