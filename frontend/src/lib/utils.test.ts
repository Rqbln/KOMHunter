import { describe, it, expect, setSystemTime } from "bun:test";
import { formatTime, formatDistance, parseJwt, isTokenExpired } from "./utils";

describe("formatTime", () => {
  it("formats zero as 0:00", () => {
    expect(formatTime(0)).toBe("0:00");
  });

  it("clamps negative values to 0:00", () => {
    expect(formatTime(-5)).toBe("0:00");
  });

  it("formats seconds under a minute", () => {
    expect(formatTime(59)).toBe("0:59");
  });

  it("formats exactly one minute", () => {
    expect(formatTime(60)).toBe("1:00");
  });

  it("formats just under an hour without hours part", () => {
    expect(formatTime(3599)).toBe("59:59");
  });

  it("formats exactly one hour", () => {
    expect(formatTime(3600)).toBe("1:00:00");
  });

  it("zero-pads minutes and seconds with hours", () => {
    expect(formatTime(3661)).toBe("1:01:01");
  });
});

describe("formatDistance", () => {
  it("formats zero meters", () => {
    expect(formatDistance(0)).toBe("0 m");
  });

  it("rounds sub-kilometer distances to whole meters", () => {
    expect(formatDistance(999.4)).toBe("999 m");
  });

  it("switches to km at exactly 1000 m", () => {
    expect(formatDistance(1000)).toBe("1.0 km");
  });

  it("formats kilometers with one decimal", () => {
    expect(formatDistance(2340)).toBe("2.3 km");
  });
});

/** Build an unsigned JWT-shaped token with the given payload */
function makeJwt(payload: Record<string, unknown>): string {
  const encode = (obj: Record<string, unknown>) =>
    btoa(JSON.stringify(obj))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");
  return `${encode({ alg: "HS256", typ: "JWT" })}.${encode(payload)}.signature`;
}

describe("parseJwt", () => {
  it("decodes the payload of a valid JWT", () => {
    const token = makeJwt({ sub: "12345", exp: 1234567890 });
    expect(parseJwt(token)).toEqual({ sub: "12345", exp: 1234567890 });
  });

  it("returns null for garbage input", () => {
    expect(parseJwt("not-a-jwt")).toBeNull();
    expect(parseJwt("")).toBeNull();
    expect(parseJwt("a.###.c")).toBeNull();
  });
});

describe("isTokenExpired", () => {
  const NOW_SECONDS = 1_700_000_000;

  it("applies a 5 minute buffer around expiry", () => {
    setSystemTime(new Date(NOW_SECONDS * 1000));
    try {
      // Expired long ago
      expect(isTokenExpired(NOW_SECONDS - 1000)).toBe(true);
      // Expires now
      expect(isTokenExpired(NOW_SECONDS)).toBe(true);
      // Inside the 5 min buffer -> treated as expired
      expect(isTokenExpired(NOW_SECONDS + 299)).toBe(true);
      // Exactly at the buffer edge -> not expired (strict >)
      expect(isTokenExpired(NOW_SECONDS + 300)).toBe(false);
      // Comfortably valid
      expect(isTokenExpired(NOW_SECONDS + 3600)).toBe(false);
    } finally {
      setSystemTime();
    }
  });
});
