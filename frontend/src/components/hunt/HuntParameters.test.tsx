import { describe, it, expect, beforeEach, afterEach } from "bun:test";
import { useState } from "react";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { HuntParameters } from "./HuntParameters";
import type { HuntParameters as HuntParamsType } from "@/types";

// React 19's act() requires this flag to be set on the global.
(globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT: boolean })
  .IS_REACT_ACT_ENVIRONMENT = true;

const PARIS = { lat: 48.8566, lon: 2.3522 };
const LYON = { lat: 45.764, lon: 4.8357 };

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(async () => {
  await act(async () => {
    root.unmount();
  });
  container.remove();
});

function clickStartHunt() {
  const btn = Array.from(container.querySelectorAll("button")).find((b) =>
    b.textContent?.includes("Start Hunt")
  );
  if (!btn) throw new Error("Start Hunt button not found");
  btn.dispatchEvent(new MouseEvent("click", { bubbles: true }));
}

describe("HuntParameters (controlled search center)", () => {
  it("submits the coordinates it is given as props, not a private default", async () => {
    const submitted: HuntParamsType[] = [];

    await act(async () => {
      root.render(
        <HuntParameters
          onSubmit={(p) => submitted.push(p)}
          location="45.7640, 4.8357"
          latitude={LYON.lat}
          longitude={LYON.lon}
          onLocationChange={() => {}}
        />
      );
    });

    await act(async () => {
      clickStartHunt();
    });

    expect(submitted).toHaveLength(1);
    expect(submitted[0].latitude).toBe(LYON.lat);
    expect(submitted[0].longitude).toBe(LYON.lon);
  });

  it("a map recenter changes the area the next hunt searches", async () => {
    // Regression: previously the form kept its own coordinates state that the
    // map click never touched, so recentering was silently discarded. Here the
    // parent owns the center (as the page does) and a "map click" updates it
    // directly (mirroring handleCenterChange, NOT the geocoding path).
    const submitted: HuntParamsType[] = [];

    function Harness() {
      const [center, setCenter] = useState(PARIS);
      const [location, setLocation] = useState("Paris, France");
      return (
        <>
          <button
            data-testid="map-click"
            onClick={() => {
              setCenter(LYON);
              setLocation("45.7640, 4.8357");
            }}
          >
            recenter
          </button>
          <HuntParameters
            onSubmit={(p) => submitted.push(p)}
            location={location}
            latitude={center.lat}
            longitude={center.lon}
            onLocationChange={(loc, lat, lon) => {
              setLocation(loc);
              setCenter({ lat, lon });
            }}
          />
        </>
      );
    }

    await act(async () => {
      root.render(<Harness />);
    });

    // First hunt: searches the initial center (Paris).
    await act(async () => {
      clickStartHunt();
    });
    expect(submitted).toHaveLength(1);
    expect(submitted[0].latitude).toBe(PARIS.lat);
    expect(submitted[0].longitude).toBe(PARIS.lon);

    // Click the map to recenter on Lyon, then hunt again WITHOUT editing the form.
    await act(async () => {
      container
        .querySelector('[data-testid="map-click"]')!
        .dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    await act(async () => {
      clickStartHunt();
    });

    // The second hunt must search Lyon — the recentered area — not stale Paris.
    expect(submitted).toHaveLength(2);
    expect(submitted[1].latitude).toBe(LYON.lat);
    expect(submitted[1].longitude).toBe(LYON.lon);
  });
});
