import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clear_token, get_token, set_token } from "../../src/utils/storage.js";

const TOKEN_KEY = "personal_blog.access_token";

describe("utils/storage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it("guarda y recupera el mismo token", () => {
    set_token("abc.def.ghi");
    expect(get_token()).toBe("abc.def.ghi");
  });

  it("devuelve null cuando no hay token", () => {
    expect(get_token()).toBeNull();
  });

  it("devuelve null después de limpiar", () => {
    set_token("abc.def.ghi");
    clear_token();
    expect(get_token()).toBeNull();
  });

  it("solo persiste la cadena del token bajo la clave con namespace", () => {
    set_token("abc.def.ghi");

    expect(window.localStorage.length).toBe(1);
    expect(window.localStorage.key(0)).toBe(TOKEN_KEY);
    expect(window.localStorage.getItem(TOKEN_KEY)).toBe("abc.def.ghi");
  });

  it("no lanza y devuelve null si la lectura del almacenamiento falla", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("storage unavailable");
    });

    expect(() => get_token()).not.toThrow();
    expect(get_token()).toBeNull();
  });

  it("no lanza si la escritura del almacenamiento falla", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("quota exceeded");
    });

    expect(() => set_token("abc.def.ghi")).not.toThrow();
  });

  it("ignora valores que no son cadenas no vacías", () => {
    set_token("");
    set_token(null);

    expect(window.localStorage.length).toBe(0);
    expect(get_token()).toBeNull();
  });
});
