import { ChatInterface } from "@/components/chat/chat-interface";
import { Hero } from "@/components/hero";
import { Navbar } from "@/components/navbar";

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden">
      <Navbar />
      <Hero />
      <section id="query" className="relative mx-auto w-full max-w-5xl px-5 pb-16 sm:px-8">
        <ChatInterface />
      </section>
      <footer className="mx-auto flex w-full max-w-5xl items-center justify-between border-t border-white/[0.07] px-5 py-8 text-xs text-[#86868B] sm:px-8">
        <span>© {new Date().getFullYear()} SatQuery AI</span><span>Earth observation, in conversation.</span>
      </footer>
    </main>
  );
}
