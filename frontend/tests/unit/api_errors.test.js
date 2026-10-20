import { describe, expect, it } from "vitest";
import { normalize } from "../../src/utils/api_errors.js";
import {
  ARTICLE_NOT_FOUND,
  FORBIDDEN,
  GENERIC_ERROR,
  INVALID_CREDENTIALS,
} from "../../src/utils/messages.js";

describe("utils/api_errors · normalize", () => {
  it("asocia duplicate_username al campo username", () => {
    expect(normalize(409, "duplicate_username", "Username already registered.")).toEqual({
      status: 409,
      code: "duplicate_username",
      globalMessage: "Username already registered.",
      fieldErrors: { username: "Username already registered." },
    });
  });

  it("asocia duplicate_email al campo email", () => {
    expect(normalize(409, "duplicate_email", "Email already registered.")).toEqual({
      status: 409,
      code: "duplicate_email",
      globalMessage: "Email already registered.",
      fieldErrors: { email: "Email already registered." },
    });
  });

  it("mapea invalid_credentials a un único mensaje genérico", () => {
    const result = normalize(401, "invalid_credentials", "Invalid credentials.");

    expect(result).toEqual({
      status: 401,
      code: "invalid_credentials",
      globalMessage: INVALID_CREDENTIALS,
      fieldErrors: {},
    });
    expect(result.globalMessage.toLowerCase()).not.toContain("username");
    expect(result.globalMessage.toLowerCase()).not.toContain("email");
  });

  it("mapea validation_error a errores por campo conservando el texto exacto", () => {
    expect(normalize(400, "validation_error", "title must be 8-20 characters.")).toEqual({
      status: 400,
      code: "validation_error",
      globalMessage: "title must be 8-20 characters.",
      fieldErrors: { title: "title must be 8-20 characters." },
    });

    expect(normalize(400, "validation_error", "Username must not contain whitespace.")).toEqual({
      status: 400,
      code: "validation_error",
      globalMessage: "Username must not contain whitespace.",
      fieldErrors: { username: "Username must not contain whitespace." },
    });
  });

  it("no inventa campo para un validation_error sin prefijo conocido", () => {
    expect(normalize(400, "validation_error", "Invalid input.")).toEqual({
      status: 400,
      code: "validation_error",
      globalMessage: "Invalid input.",
      fieldErrors: {},
    });
  });

  it("mapea un detail en formato de lista a errores por campo", () => {
    const detail = [{ loc: ["body", "password"], msg: "Password is required." }];

    expect(normalize(400, "validation_error", detail)).toEqual({
      status: 400,
      code: "validation_error",
      globalMessage: GENERIC_ERROR,
      fieldErrors: { password: "Password is required." },
    });
  });

  it("normaliza un fallo de red a network_error", () => {
    expect(normalize(0, undefined, undefined)).toEqual({
      status: 0,
      code: "network_error",
      globalMessage: GENERIC_ERROR,
      fieldErrors: {},
    });

    expect(normalize(0, "network_error", "timeout")).toEqual({
      status: 0,
      code: "network_error",
      globalMessage: GENERIC_ERROR,
      fieldErrors: {},
    });
  });

  it("oculta el detalle técnico de los errores 5xx", () => {
    expect(normalize(503, "internal_error", "database connection failed")).toEqual({
      status: 503,
      code: "internal_error",
      globalMessage: GENERIC_ERROR,
      fieldErrors: {},
    });
  });

  it("usa el copy centralizado para forbidden y article_not_found", () => {
    expect(normalize(403, "forbidden", "Admin role required.")).toEqual({
      status: 403,
      code: "forbidden",
      globalMessage: FORBIDDEN,
      fieldErrors: {},
    });

    expect(normalize(404, "article_not_found", "Article not found.")).toEqual({
      status: 404,
      code: "article_not_found",
      globalMessage: ARTICLE_NOT_FOUND,
      fieldErrors: {},
    });
  });

  it("conserva el detail de códigos desconocidos y cae al genérico sin detalle", () => {
    expect(normalize(400, "weird_code", "Something specific.")).toEqual({
      status: 400,
      code: "weird_code",
      globalMessage: "Something specific.",
      fieldErrors: {},
    });

    expect(normalize(400, undefined, "")).toEqual({
      status: 400,
      code: "unknown_error",
      globalMessage: GENERIC_ERROR,
      fieldErrors: {},
    });
  });
});
