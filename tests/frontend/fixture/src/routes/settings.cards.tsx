// a TanStack FILE route: the export is always `Route`; the URL lives in the factory's literal (tier0 review 2026-09-07)
import { createFileRoute } from "@tanstack/react-router";

function Cards() {
  return <div>cards</div>;
}

export const Route = createFileRoute("/settings/cards")({ component: Cards });
