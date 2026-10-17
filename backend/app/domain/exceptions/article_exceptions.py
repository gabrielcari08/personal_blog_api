"""Excepciones del dominio de articulos.

Define los errores de negocio para crear, ver, editar y eliminar articulos.
No incluye detalles tecnicos ni mensajes especificos de infraestructura.
"""


class ArticleValidationException(Exception):
    """Error de validacion de titulo o texto (mensajes exactos de la spec)."""

    pass


class ArticleNotFoundException(Exception):
    """El articulo objetivo no existe."""

    pass


class ArticleForbiddenException(Exception):
    """Accion no permitida: solo el autor o un administrador puede mutar."""

    pass
