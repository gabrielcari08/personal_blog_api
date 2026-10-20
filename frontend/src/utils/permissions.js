/**
 * Indica si la sesión pertenece a un administrador.
 * @param {{ role?: string } | null | undefined} session
 * @returns {boolean}
 */
export function is_admin(session) {
  return Boolean(session) && session.role === "ADMIN";
}

/**
 * Indica si la sesión puede editar o eliminar el artículo dado.
 * Un ADMIN puede con cualquiera; un USER solo con los propios.
 * @param {{ user_id?: number | string } | null | undefined} article
 * @param {{ user_id?: number | string, role?: string } | null | undefined} session
 * @returns {boolean}
 */
export function can_manage_article(article, session) {
  if (!session) {
    return false;
  }

  if (is_admin(session)) {
    return true;
  }

  if (!article || session.user_id == null || article.user_id == null) {
    return false;
  }

  // El claim `sub` del token llega como string y el backend devuelve números.
  return String(session.user_id) === String(article.user_id);
}
