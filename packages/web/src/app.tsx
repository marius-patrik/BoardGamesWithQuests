import { ArrowUpRight, Layers3, ServerCog, Smartphone, Sparkles } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import { Button } from "@/components/ui/button";

const systems = [
  { title: "Web", detail: "React / TypeScript / shadcn/ui", icon: Layers3 },
  { title: "API", detail: "FastAPI on Vercel", icon: ServerCog },
  { title: "Native", detail: "Tauri on five platforms", icon: Smartphone },
];

export function App() {
  const [details, setDetails] = useState(false);
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-5 py-10 md:px-12">
      <header className="flex items-center justify-between border-b border-border pb-6">
        <div className="flex items-center gap-3 font-semibold tracking-tight">
          <span className="grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground">
            <Layers3 size={19} aria-hidden="true" />
          </span>
          BoardGamesWithQuests
        </div>
        <span className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground">
          Platform bootstrap
        </span>
      </header>
      <section className="flex flex-1 flex-col justify-center py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="max-w-3xl"
        >
          <div className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
            <Sparkles size={16} aria-hidden="true" />
            Shared web and native application
          </div>
          <h1 className="text-5xl font-semibold tracking-tight md:text-7xl">
            One platform.<br />
            <span className="text-muted-foreground">Every board.</span>
          </h1>
          <p className="mt-7 max-w-xl text-lg leading-relaxed text-muted-foreground">
            The application shell is ready for game and session integration.
            Multiplayer gameplay is not implemented in this bootstrap.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button onClick={() => setDetails((previous) => !previous)}>
              {details ? "Hide architecture" : "View architecture"}
            </Button>
            <Button asChild variant="outline">
              <a href="https://github.com/marius-patrik/BoardGamesWithQuests" target="_blank" rel="noreferrer">
                Source <ArrowUpRight size={15} aria-hidden="true" />
              </a>
            </Button>
          </div>
        </motion.div>
        <div className="mt-16 grid gap-4 md:grid-cols-3">
          {systems.map(({ title, detail, icon: Icon }, index) => (
            <motion.article
              key={title}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.09 }}
              className="rounded-2xl border border-border bg-card p-6"
            >
              <Icon size={24} className="mb-8 text-muted-foreground" aria-hidden="true" />
              <h2 className="font-semibold">{title}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{detail}</p>
            </motion.article>
          ))}
        </div>
        {details && (
          <p role="status" className="mt-5 rounded-xl border border-border bg-card p-4 text-sm text-muted-foreground">
            Browser and Tauri share this deployed React interface. Python owns future game
            decisions; FastAPI provides the API boundary; Supabase will own durable state.
          </p>
        )}
      </section>
      <footer className="border-t border-border py-6 text-xs text-muted-foreground">
        Infrastructure only — no playable games are available.
      </footer>
    </main>
  );
}
