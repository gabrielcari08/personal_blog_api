import { describe, expect, it } from "vitest";
import { can_manage_article, is_admin } from "../../src/utils/permissions.js";

const admin = { user_id: 99, role: "ADMIN" };
const owner = { user_id: 1, role: "USER" };
const other = { user_id: 2, role: "USER" };
const article = { user_id: 1 };

describe("utils/permissions · is_admin", () => {
  it("solo es true con rol ADMIN", () => {
    expect(is_admin(admin)).toBe(true);
    expect(is_admin(owner)).toBe(false);
    expect(is_admin(null)).toBe(false);
    expect(is_admin(undefined)).toBe(false);
    expect(is_admin({})).toBe(false);
  });
});

describe("utils/permissions · can_manage_article", () => {
  it("ADMIN gestiona cualquier artículo", () => {
    expect(can_manage_article(article, admin)).toBe(true);
    expect(can_manage_article({ user_id: 500 }, admin)).toBe(true);
  });

  it("USER propietario gestiona su artículo", () => {
    expect(can_manage_article(article, owner)).toBe(true);
  });

  it("USER no propietario no gestiona", () => {
    expect(can_manage_article(article, other)).toBe(false);
  });

  it("sin sesión no gestiona", () => {
    expect(can_manage_article(article, null)).toBe(false);
    expect(can_manage_article(article, undefined)).toBe(false);
  });

  it("compara ids string (claim sub) con ids numéricos del backend", () => {
    expect(can_manage_article({ user_id: 7 }, { user_id: "7", role: "USER" })).toBe(true);
    expect(can_manage_article({ user_id: 7 }, { user_id: "8", role: "USER" })).toBe(false);
  });

  it("no gestiona artículos ausentes", () => {
    expect(can_manage_article(null, owner)).toBe(false);
  });
});
