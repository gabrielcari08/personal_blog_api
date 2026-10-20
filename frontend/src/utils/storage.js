// Clave única donde se persiste el token de sesión (con namespace).
const TOKEN_KEY = "personal_blog.access_token";

/**
 * Devuelve el almacenamiento local de forma segura.
 * En entornos sin `localStorage` (SSR, navegador restringido) devuelve null en
 * lugar de lanzar.
 * @returns {Storage | null}
 */
function get_storage() {
  try {
    if (typeof window === "undefined" || !window.localStorage) {
      return null;
    }
    return window.localStorage;
  } catch {
    return null;
  }
}

/**
 * Recupera el token persistido.
 * @returns {string | null} El token, o null si no existe o no hay almacenamiento.
 */
export function get_token() {
  const storage = get_storage();
  if (!storage) {
    return null;
  }

  try {
    return storage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

/**
 * Persiste el token de sesión. Solo se guarda la cadena del token, nunca la
 * contraseña ni datos del usuario.
 * @param {string} token
 * @returns {void}
 */
export function set_token(token) {
  const storage = get_storage();
  if (!storage || typeof token !== "string" || token.length === 0) {
    return;
  }

  try {
    storage.setItem(TOKEN_KEY, token);
  } catch {
    // Un fallo de escritura (cuota o permisos) se ignora: la app sigue sin sesión.
  }
}

/**
 * Elimina el token persistido.
 * @returns {void}
 */
export function clear_token() {
  const storage = get_storage();
  if (!storage) {
    return;
  }

  try {
    storage.removeItem(TOKEN_KEY);
  } catch {
    // Se ignora a propósito: no hay nada que recuperar de un fallo al limpiar.
  }
}
