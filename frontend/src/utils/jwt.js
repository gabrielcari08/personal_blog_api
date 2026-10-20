/**
 * Decodifica el payload de un JWT sin verificar la firma.
 *
 * Solo se usa para leer claims en el cliente; la validación real de la firma
 * corresponde al backend. Un token malformado devuelve null en lugar de lanzar.
 *
 * @param {string} token
 * @returns {{ user_id: number | string | null, username: string | null, role: string | null, exp: number | null } | null}
 */
export function decode(token) {
  if (typeof token !== "string") {
    return null;
  }

  const parts = token.split(".");
  if (parts.length !== 3 || !parts[1]) {
    return null;
  }

  try {
    const normalized = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const binary = globalThis.atob(padded);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    const claims = JSON.parse(new globalThis.TextDecoder().decode(bytes));

    if (claims === null || typeof claims !== "object" || Array.isArray(claims)) {
      return null;
    }

    return {
      user_id: claims.user_id ?? null,
      username: claims.username ?? null,
      role: claims.role ?? null,
      exp: claims.exp ?? null,
    };
  } catch {
    return null;
  }
}

/**
 * Indica si un conjunto de claims está expirado comparando `exp` con la hora
 * actual. Un `exp` ausente o inválido se considera expirado.
 * @param {{ exp?: number | null } | null | undefined} claims
 * @returns {boolean}
 */
export function is_expired(claims) {
  if (!claims || typeof claims.exp !== "number") {
    return true;
  }

  const now_in_seconds = Math.floor(Date.now() / 1000);
  return claims.exp <= now_in_seconds;
}
