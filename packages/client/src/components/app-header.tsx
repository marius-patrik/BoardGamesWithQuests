import { LogOut } from "lucide-react";
import { Link } from "wouter";
import { Button } from "@/components/ui/button";

export function AppHeader({ signedIn, busy, onSignOut }: {
  signedIn: boolean;
  busy: boolean;
  onSignOut: () => void;
}) {
  return (
    <header className="flex items-center justify-between border-b border-border pb-6">
      <Link href="/" className="flex items-center gap-3 text-sm font-semibold tracking-wide sm:text-base">
        <img src="/icon.svg" alt="" className="size-9 rounded-lg" />
        BoardGamesWithQuests
      </Link>
      {signedIn && <Button variant="outline" size="sm" disabled={busy} onClick={onSignOut}>
        <LogOut size={16} /> Sign out
      </Button>}
    </header>
  );
}
