// Formateador reutilizable: fecha y hora legibles en la zona horaria local.
const formatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

/**
 * Convierte una marca de tiempo ISO-8601 (UTC) a texto en la zona horaria local.
 * Devuelve cadena vacía para entradas ausentes o inválidas en lugar de lanzar.
 * @param {string | null | undefined} iso_utc
 * @returns {string}
 */
export function format_created_at(iso_utc) {
  if (typeof iso_utc !== "string" || iso_utc.trim() === "") {
    return "";
  }

  const date = new Date(iso_utc);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return formatter.format(date);
}
