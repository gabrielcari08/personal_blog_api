import { describe, expect, it } from "vitest";
import { format_created_at } from "../../src/utils/date.js";

describe("utils/date", () => {
  it("formatea una fecha ISO UTC válida sin lanzar", () => {
    const result = format_created_at("2026-06-15T12:30:00Z");

    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
    expect(result).toContain("2026");
  });

  it("devuelve cadena vacía para entradas inválidas o ausentes", () => {
    expect(format_created_at("no-es-fecha")).toBe("");
    expect(format_created_at("")).toBe("");
    expect(format_created_at("   ")).toBe("");
    expect(format_created_at(null)).toBe("");
    expect(format_created_at(undefined)).toBe("");
    expect(format_created_at(123)).toBe("");
  });
});
