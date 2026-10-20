import { afterEach, describe, expect, it, vi } from "vitest";
import { decode, is_expired } from "../../src/utils/jwt.js";

// Construye un JWT sin firma real (header.payload.signature) para probar la
// decodificación. La firma no se valida en el cliente.
function make_token(payload) {
  const encode = (value) =>
    globalThis
      .btoa(JSON.stringify(value))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");

  return `${encode({ alg: "HS256", typ: "JWT" })}.${encode(payload)}.signature`;
}

describe("utils/jwt", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("decodifica los cuatro claims de un token válido (sub del backend)", () => {
    const token = make_token({
      sub: "42",
      username: "user01AB",
      role: "ADMIN",
      exp: 2_000_000_000,
    });

    expect(decode(token)).toEqual({
      user_id: "42",
      username: "user01AB",
      role: "ADMIN",
      exp: 2_000_000_000,
    });
  });

  it("admite el claim user_id cuando está presente", () => {
    const token = make_token({
      user_id: 42,
      username: "user01AB",
      role: "USER",
      exp: 2_000_000_000,
    });

    expect(decode(token).user_id).toBe(42);
  });

  it("devuelve null para un token malformado o vacío", () => {
    expect(decode("no-es-un-jwt")).toBeNull();
    expect(decode("")).toBeNull();
    expect(decode("solo.dos")).toBeNull();
    expect(decode("a.@@@.c")).toBeNull();
    expect(decode(null)).toBeNull();
  });

  it("devuelve null si el payload no es un objeto JSON", () => {
    const token = make_token([1, 2, 3]);
    expect(decode(token)).toBeNull();
  });

  it("detecta un token expirado", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T00:00:00Z"));

    const past_exp = Math.floor(Date.now() / 1000) - 60;
    expect(is_expired({ exp: past_exp })).toBe(true);
  });

  it("no marca como expirado un token futuro", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T00:00:00Z"));

    const future_exp = Math.floor(Date.now() / 1000) + 60;
    expect(is_expired({ exp: future_exp })).toBe(false);
  });

  it("considera expirado un exp ausente o inválido", () => {
    expect(is_expired(null)).toBe(true);
    expect(is_expired({})).toBe(true);
    expect(is_expired({ exp: "no-numero" })).toBe(true);
  });
});
