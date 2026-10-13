import type React from "react";
import { createRoot } from "react-dom/client";

function App(): React.JSX.Element {
  return (
    <main>
      <h1>BoardGamesWithQuests</h1>
      <p>Online chess and draughts implementation is in progress.</p>
      <p>No game can be started yet; this page does not simulate gameplay.</p>
    </main>
  );
}

const mount = document.getElementById("root");
if (!mount) throw new Error("Missing React root element");
createRoot(mount).render(<App />);
