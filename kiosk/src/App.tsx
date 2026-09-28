import { GatePage } from "./pages/GatePage";
/** Kiosk shell: a single full-screen gate page for door staff. */
export function App() {
  return (
    <div className="kiosk">
      <header className="kiosk-bar">
        <strong>Concourse Gate</strong>
        <span>Door scanning kiosk</span>
      </header>
      <GatePage />
    </div>
  );
}
