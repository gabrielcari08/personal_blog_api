import { ARTICLE_NOT_FOUND, FORBIDDEN, GENERIC_ERROR, INVALID_CREDENTIALS } from "./messages.js";

// Códigos de duplicado que se asocian directamente a un campo del formulario.
const DUPLICATE_FIELD_BY_CODE = {
  duplicate_username: "username",
  duplicate_email: "email",
};

// Campos conocidos del backend para el mapeo best-effort de `validation_error`.
const FIELD_PREFIXES = ["username", "email", "password", "identifier", "title", "text", "role"];

/**
 * Extrae errores por campo de un `detail` de validación (best-effort).
 * @param {unknown} detail
 * @returns {Record<string, string>}
 */
function parse_detail_fields(detail) {
  if (Array.isArray(detail)) {
    const errors = {};
    for (const item of detail) {
      const location = Array.isArray(item?.loc) ? item.loc : [];
      const field = location[location.length - 1];
      if (typeof field === "string" && typeof item?.msg === "string") {
        errors[field] = item.msg;
      }
    }
    return errors;
  }

  if (typeof detail !== "string") {
    return {};
  }

  const message = detail.trim();
  if (message === "") {
    return {};
  }

  const prefix = message.split(/\s+/)[0]?.toLowerCase();
  if (FIELD_PREFIXES.includes(prefix)) {
    return { [prefix]: message };
  }

  return {};
}

/**
 * Normaliza un fallo del backend (o de red) a la forma `ApiError`.
 * @param {number} status
 * @param {string | undefined} code
 * @param {unknown} detail
 * @returns {{ status: number, code: string, globalMessage: string, fieldErrors: Record<string, string> }}
 */
export function normalize(status, code, detail) {
  // Sin respuesta HTTP: error de red o timeout.
  if (!status || code === "network_error") {
    return {
      status: 0,
      code: "network_error",
      globalMessage: GENERIC_ERROR,
      fieldErrors: {},
    };
  }

  // Errores de servidor: nunca se muestra el detalle técnico.
  if (status >= 500) {
    return {
      status,
      code: typeof code === "string" && code !== "" ? code : "server_error",
      globalMessage: GENERIC_ERROR,
      fieldErrors: {},
    };
  }

  const field_errors = {};
  const duplicate_field = DUPLICATE_FIELD_BY_CODE[code];

  if (duplicate_field) {
    field_errors[duplicate_field] =
      typeof detail === "string" && detail.trim() !== "" ? detail : GENERIC_ERROR;
  } else if (code === "validation_error") {
    Object.assign(field_errors, parse_detail_fields(detail));
  }

  // BR-3: se conserva el mensaje exacto del backend cuando existe.
  let global_message = typeof detail === "string" && detail.trim() !== "" ? detail : GENERIC_ERROR;

  if (code === "invalid_credentials") {
    global_message = INVALID_CREDENTIALS;
  } else if (code === "forbidden") {
    global_message = FORBIDDEN;
  } else if (code === "article_not_found") {
    global_message = ARTICLE_NOT_FOUND;
  }

  return {
    status,
    code: typeof code === "string" && code !== "" ? code : "unknown_error",
    globalMessage: global_message,
    fieldErrors: field_errors,
  };
}
