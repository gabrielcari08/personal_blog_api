// Límites alineados con el backend (ver plan §3.4).
const USERNAME_MIN_LENGTH = 8;
const USERNAME_MAX_LENGTH = 20;
const PASSWORD_MIN_LENGTH = 8;
const PASSWORD_MAX_LENGTH = 20;
const TITLE_MIN_LENGTH = 8;
const TITLE_MAX_LENGTH = 20;
const TEXT_MIN_LENGTH = 10;
const TEXT_MAX_LENGTH = 300;

// Forma estándar mínima de un correo.
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Longitud en puntos de código: un emoji cuenta como un solo carácter.
 * @param {string} value
 * @returns {number}
 */
function char_length(value) {
  return [...value].length;
}

/**
 * Indica si el valor es una cadena no vacía.
 * @param {unknown} value
 * @returns {boolean}
 */
function is_non_empty_string(value) {
  return typeof value === "string" && value !== "";
}

/**
 * Valida los datos del registro replicando las reglas del backend.
 * @param {{ username?: string, email?: string, password?: string } | null | undefined} values
 * @returns {{ username?: string, email?: string, password?: string }}
 */
export function validate_register(values = {}) {
  const errors = {};
  const { username, email, password } = values ?? {};

  // Username: requerido, sin blancos y con longitud cruda 8-20.
  if (!is_non_empty_string(username)) {
    errors.username = "Username is required.";
  } else if (/\s/.test(username)) {
    errors.username = "Username must not contain whitespace.";
  } else {
    const length = char_length(username);
    if (length < USERNAME_MIN_LENGTH || length > USERNAME_MAX_LENGTH) {
      errors.username = "Username must be 8-20 characters.";
    }
  }

  // Email: requerido y con forma válida; se valida recortado.
  if (typeof email !== "string" || email.trim() === "") {
    errors.email = "Email is required.";
  } else if (!EMAIL_PATTERN.test(email.trim())) {
    errors.email = "Email must be a valid email address.";
  }

  // Password: requerido y con longitud cruda 8-20 (sin recortar).
  if (!is_non_empty_string(password)) {
    errors.password = "Password is required.";
  } else {
    const length = char_length(password);
    if (length < PASSWORD_MIN_LENGTH || length > PASSWORD_MAX_LENGTH) {
      errors.password = "Password must be 8-20 characters.";
    }
  }

  return errors;
}

/**
 * Valida los datos del login: solo exige identificador y contraseña.
 * @param {{ identifier?: string, password?: string } | null | undefined} values
 * @returns {{ identifier?: string, password?: string }}
 */
export function validate_login(values = {}) {
  const errors = {};
  const { identifier, password } = values ?? {};

  if (!is_non_empty_string(identifier)) {
    errors.identifier = "Identifier is required.";
  }
  if (!is_non_empty_string(password)) {
    errors.password = "Password is required.";
  }

  return errors;
}

/**
 * Valida los datos de un artículo con longitudes crudas y los mensajes exactos.
 * @param {{ title?: string, text?: string } | null | undefined} values
 * @returns {{ title?: string, text?: string }}
 */
export function validate_article(values = {}) {
  const errors = {};
  const { title, text } = values ?? {};

  // Título: longitud cruda 8-20, sin recortar; el vacío cae en el mismo rango.
  if (typeof title !== "string") {
    errors.title = "title must be 8-20 characters";
  } else {
    const title_length = char_length(title);
    if (title_length < TITLE_MIN_LENGTH || title_length > TITLE_MAX_LENGTH) {
      errors.title = "title must be 8-20 characters";
    }
  }

  // Texto: solo la cadena exactamente vacía es "requerida"; los blancos cuentan.
  if (typeof text !== "string" || text === "") {
    errors.text = "text is required";
  } else {
    const text_length = char_length(text);
    if (text_length < TEXT_MIN_LENGTH || text_length > TEXT_MAX_LENGTH) {
      errors.text = "text must be 10-300 characters";
    }
  }

  return errors;
}
