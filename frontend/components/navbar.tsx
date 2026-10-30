import { Github, Orbit } from "lucide-react";

export function Navbar() {
  return <header className="relative z-20 mx-auto flex h-20 max-w-6xl items-center justify-between px-5 sm:px-8">
    <a href="#top" className="focus-ring flex items-center gap-2.5 rounded-lg text-sm font-semibold tracking-tight"><span className="grid size-8 place-items-center rounded-full bg-[#0A84FF] shadow-[0_0_24px_rgba(10,132,255,.45)]"><Orbit size={17} /></span>SatQuery AI</a>
    <nav className="hidden items-center gap-7 text-sm text-[#86868B] sm:flex"><a className="transition hover:text-[#F5F5F7]" href="#about">About</a><a className="transition hover:text-[#F5F5F7]" href="#technology">Technology</a><a className="focus-ring flex items-center gap-2 rounded-md transition hover:text-[#F5F5F7]" href="https://github.com" target="_blank" rel="noreferrer"><Github size={15} />GitHub</a></nav>
  </header>;
}
