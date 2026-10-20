import { describe, expect, it } from "vitest";
import { validate_article, validate_login, validate_register } from "../../src/utils/validators.js";

const valid_register = {
  username: "user01AB",
  email: "user@mail.com",
  password: "password1",
};

const valid_article = {
  title: "My first post",
  text: "This is a valid article text.",
};

describe("utils/validators · validate_register", () => {
  it("acepta datos válidos", () => {
    expect(validate_register(valid_register)).toEqual({});
  });

  it("exige username, email y password", () => {
    expect(validate_register({})).toEqual({
      username: "Username is required.",
      email: "Email is required.",
      password: "Password is required.",
    });
  });

  it("rechaza blancos en cualquier posición del username", () => {
    for (const username of ["my user01", " user01AB", "user01AB "]) {
      expect(validate_register({ ...valid_register, username })).toEqual({
        username: "Username must not contain whitespace.",
      });
    }
  });

  it("aplica los límites 7/8/20/21 del username", () => {
    const short = validate_register({ ...valid_register, username: "a".repeat(7) });
    const min = validate_register({ ...valid_register, username: "a".repeat(8) });
    const max = validate_register({ ...valid_register, username: "a".repeat(20) });
    const long = validate_register({ ...valid_register, username: "a".repeat(21) });

    expect(short.username).toBe("Username must be 8-20 characters.");
    expect(min.username).toBeUndefined();
    expect(max.username).toBeUndefined();
    expect(long.username).toBe("Username must be 8-20 characters.");
  });

  it("cuenta un emoji como un carácter en el username", () => {
    expect(validate_register({ ...valid_register, username: "😀".repeat(8) })).toEqual({});
    expect(validate_register({ ...valid_register, username: "😀".repeat(7) })).toEqual({
      username: "Username must be 8-20 characters.",
    });
  });

  it("valida la forma del email y recorta sus extremos", () => {
    expect(validate_register({ ...valid_register, email: "  user@mail.com  " })).toEqual({});
    expect(validate_register({ ...valid_register, email: "no-es-email" })).toEqual({
      email: "Email must be a valid email address.",
    });
    expect(validate_register({ ...valid_register, email: "   " })).toEqual({
      email: "Email is required.",
    });
  });

  it("aplica los límites 7/8/20/21 del password", () => {
    const short = validate_register({ ...valid_register, password: "a".repeat(7) });
    const min = validate_register({ ...valid_register, password: "a".repeat(8) });
    const max = validate_register({ ...valid_register, password: "a".repeat(20) });
    const long = validate_register({ ...valid_register, password: "a".repeat(21) });

    expect(short.password).toBe("Password must be 8-20 characters.");
    expect(min.password).toBeUndefined();
    expect(max.password).toBeUndefined();
    expect(long.password).toBe("Password must be 8-20 characters.");
  });

  it("no recorta el password antes de medirlo", () => {
    // 8 caracteres crudos; recortado quedaría en 4 y sería inválido.
    expect(validate_register({ ...valid_register, password: "  pass  " })).toEqual({});
  });
});

describe("utils/validators · validate_login", () => {
  it("solo exige identificador y contraseña", () => {
    expect(validate_login({})).toEqual({
      identifier: "Identifier is required.",
      password: "Password is required.",
    });
  });

  it("acepta credenciales presentes sin validar su formato", () => {
    expect(validate_login({ identifier: "user01AB", password: "x" })).toEqual({});
    expect(validate_login({ identifier: "user@mail.com", password: "x" })).toEqual({});
    expect(validate_login({ identifier: " user01AB ", password: "x" })).toEqual({});
  });
});

describe("utils/validators · validate_article", () => {
  it("acepta datos válidos", () => {
    expect(validate_article(valid_article)).toEqual({});
  });

  it("usa el mensaje exacto del título fuera de rango", () => {
    expect(validate_article({ title: "a".repeat(7), text: valid_article.text })).toEqual({
      title: "title must be 8-20 characters",
    });
    expect(validate_article({ title: "a".repeat(21), text: valid_article.text })).toEqual({
      title: "title must be 8-20 characters",
    });
    expect(validate_article({ title: "", text: valid_article.text })).toEqual({
      title: "title must be 8-20 characters",
    });
  });

  it("aplica los límites 8/20 del título y no recorta blancos", () => {
    expect(validate_article({ title: "a".repeat(8), text: valid_article.text })).toEqual({});
    expect(validate_article({ title: "a".repeat(20), text: valid_article.text })).toEqual({});
    expect(validate_article({ title: "        ", text: valid_article.text })).toEqual({});
  });

  it("cuenta un emoji como un carácter en el título", () => {
    expect(validate_article({ title: "😀".repeat(8), text: valid_article.text })).toEqual({});
    expect(validate_article({ title: "😀".repeat(7), text: valid_article.text })).toEqual({
      title: "title must be 8-20 characters",
    });
  });

  it("exige el texto con el mensaje exacto", () => {
    expect(validate_article({ title: valid_article.title, text: "" })).toEqual({
      text: "text is required",
    });
    expect(validate_article({ title: valid_article.title })).toEqual({
      text: "text is required",
    });
  });

  it("aplica los límites 9/10/300/301 del texto sin recortar", () => {
    expect(validate_article({ title: valid_article.title, text: "a".repeat(9) })).toEqual({
      text: "text must be 10-300 characters",
    });
    expect(validate_article({ title: valid_article.title, text: "a".repeat(10) })).toEqual({});
    expect(validate_article({ title: valid_article.title, text: "a".repeat(300) })).toEqual({});
    expect(validate_article({ title: valid_article.title, text: "a".repeat(301) })).toEqual({
      text: "text must be 10-300 characters",
    });
  });

  it("cuenta los blancos del texto como caracteres (no los recorta)", () => {
    expect(validate_article({ title: valid_article.title, text: " ".repeat(9) })).toEqual({
      text: "text must be 10-300 characters",
    });
    expect(validate_article({ title: valid_article.title, text: " ".repeat(10) })).toEqual({});
  });
});
