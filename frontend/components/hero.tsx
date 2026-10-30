"use client";

import dynamic from "next/dynamic";
import { ArrowDown } from "lucide-react";
import { motion } from "motion/react";

const EarthScene = dynamic(() => import("./three/earth-scene").then((module) => module.EarthScene), { ssr: false });

export function Hero() {
  return <section id="top" className="relative -mt-20 flex min-h-[650px] items-center justify-center overflow-hidden px-5 pb-16 pt-28 sm:min-h-[720px]">
    <div className="noise pointer-events-none absolute inset-0" />
    <div className="pointer-events-none absolute inset-0 opacity-80"><EarthScene /></div>
    <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .8, ease: "easeOut" }} className="relative z-10 mx-auto max-w-3xl text-center">
      <p className="mb-6 text-[11px] font-semibold tracking-[.24em] text-[#0A84FF] sm:text-xs">TEMPORAL EARTH INTELLIGENCE</p>
      <h1 className="text-5xl font-semibold tracking-[-.055em] text-[#F5F5F7] sm:text-7xl">Ask the Earth<br />anything.</h1>
      <p className="mx-auto mt-7 max-w-xl text-base leading-7 text-[#86868B] sm:text-lg">Upload satellite imagery for land-cover, spectral, and geospatial analysis.</p>
      <a href="#query" className="focus-ring mt-10 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[.06] px-5 py-3 text-sm text-[#F5F5F7] backdrop-blur transition hover:border-white/20 hover:bg-white/[.1]">Start a query <ArrowDown size={15} /></a>
    </motion.div>
  </section>;
}
