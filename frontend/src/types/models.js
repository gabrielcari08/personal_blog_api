/**
 * Contratos de datos compartidos del frontend de Personal Blog.
 *
 * Este módulo contiene únicamente definiciones de tipos en JSDoc. No tiene
 * lógica de runtime, de modo que el mismo vocabulario se reutiliza en
 * componentes, hooks y servicios.
 */

/**
 * Unión literal de roles. El backend solo emite estos dos valores.
 * El registro siempre crea `USER`; `ADMIN` se concede por seed o promoción.
 * @typedef {"USER" | "ADMIN"} Role
 */

/**
 * Usuario autenticado tal como lo devuelve el backend (`UserOutput`).
 * @typedef {Object} User
 * @property {number | string} id - Identificador estable del usuario.
 * @property {string} username - 8-20 caracteres, sin espacios en blanco.
 * @property {string} email - Forma de visualización (recortada, con mayúsculas originales).
 * @property {Role} role - `USER` al registrarse; `ADMIN` vía seed o promoción.
 */

/**
 * Artículo tal como lo devuelve el backend (`ArticleOutput`).
 * El backend expone solo `user_id` como señal del autor; en esta versión no
 * existe un nombre visible del autor.
 * @typedef {Object} Article
 * @property {number | string} id - Identificador estable del artículo.
 * @property {string} title - 8-20 caracteres (longitud bruta, sin recorte).
 * @property {string} text - 10-300 caracteres (longitud bruta, sin recorte).
 * @property {number | string} user_id - Referencia del propietario usada para permisos.
 * @property {string} created_at - Marca ISO-8601 en UTC; se formatea en local.
 */

/**
 * Sesión del cliente derivada de los claims del token de login.
 * Solo se persiste `access_token` (ver `utils/storage.js`); el resto de campos
 * se decodifican del token, no se obtienen de un endpoint de perfil.
 * @typedef {Object} AuthSession
 * @property {string} access_token - Token bearer devuelto por el login.
 * @property {number | string} user_id - Claim `user_id` decodificado.
 * @property {string} username - Claim `username` decodificado.
 * @property {Role} role - Claim `role` decodificado.
 * @property {number} expires_at - Claim `exp` decodificado (segundos epoch).
 */

/**
 * Forma de la respuesta de login. El backend expone solo estos dos campos; los
 * datos de identidad se obtienen decodificando el token (no hay endpoint `/me`).
 * @typedef {Object} LoginResult
 * @property {string} access_token - Token bearer sin estado.
 * @property {string} token_type - Siempre `bearer` en esta versión.
 */

/**
 * Mensajes de error direccionables por campo, indexados por nombre de campo.
 * @typedef {Object.<string, string>} FieldErrors
 */

/**
 * Error de API normalizado, producido por `utils/api_errors.js`.
 * @typedef {Object} ApiError
 * @property {number} status - Estado HTTP, o 0 para fallos de red/timeout.
 * @property {string} code - Código estable del backend (p. ej. `validation_error`,
 *   `duplicate_username`, `duplicate_email`, `invalid_credentials`,
 *   `forbidden`, `article_not_found`, `network_error`).
 * @property {string} globalMessage - Mensaje legible para mostrar en página/formulario.
 * @property {FieldErrors} fieldErrors - Mensajes por campo, cuando aplican.
 */

/**
 * Estado del formulario de registro. Los valores se mantienen brutos (sin
 * recorte previo) para preservar las reglas de espacios en blanco del backend.
 * @typedef {Object} RegisterFormState
 * @property {string} username - 8-20 caracteres, sin espacios en blanco.
 * @property {string} email - Formato de email estándar válido.
 * @property {string} password - 8-20 caracteres, sin recorte.
 */

/**
 * Estado del formulario de login. `identifier` acepta el email o el username.
 * @typedef {Object} LoginFormState
 * @property {string} identifier - Email o username registrado.
 * @property {string} password - Contraseña en bruto.
 */

/**
 * Estado del formulario de creación/edición de artículos. El autor y la fecha
 * de creación nunca forman parte del payload; solo se editan title y text.
 * @typedef {Object} ArticleFormState
 * @property {string} title - 8-20 caracteres (longitud bruta).
 * @property {string} text - 10-300 caracteres (longitud bruta).
 */

// Marca el archivo como módulo ES; no se necesitan exportaciones de runtime.
export {};
