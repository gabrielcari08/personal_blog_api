"""Rutas HTTP de articulos (lectura publica, mutacion dueno o admin)."""

from fastapi import APIRouter, Depends, Response, status

from app.application.dtos.article_dtos import (
    ArticleCreateInput,
    ArticleOutput,
    ArticleUpdateInput,
)
from app.application.use_cases.article.create_article import CreateArticle
from app.application.use_cases.article.delete_article import DeleteArticle
from app.application.use_cases.article.get_article import GetArticle
from app.application.use_cases.article.list_articles import ListArticles
from app.application.use_cases.article.update_article import UpdateArticle
from app.domain.entities.user import User
from app.entrypoints.api.v1.dependencies import (
    get_create_article,
    get_current_user,
    get_delete_article,
    get_get_article,
    get_list_articles,
    get_update_article,
)

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=list[ArticleOutput])
def list_articles(
    use_case: ListArticles = Depends(get_list_articles),
) -> list[ArticleOutput]:
    """Lista publica de articulos de mas reciente a mas antiguo."""
    return use_case.execute()


@router.get("/{article_id}", response_model=ArticleOutput)
def get_article(
    article_id: int,
    use_case: GetArticle = Depends(get_get_article),
) -> ArticleOutput:
    """Detalle publico de un articulo (404 si no existe)."""
    return use_case.execute(article_id)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ArticleOutput)
def create_article(
    data: ArticleCreateInput,
    caller: User = Depends(get_current_user),
    use_case: CreateArticle = Depends(get_create_article),
) -> ArticleOutput:
    """Crea un articulo owned por el solicitante (401 sin token)."""
    return use_case.execute(caller, data)


@router.put("/{article_id}", response_model=ArticleOutput)
def update_article(
    article_id: int,
    data: ArticleUpdateInput,
    caller: User = Depends(get_current_user),
    use_case: UpdateArticle = Depends(get_update_article),
) -> ArticleOutput:
    """Reemplaza titulo y texto (autor o admin; 403 ante intento directo ajeno)."""
    return use_case.execute(caller, article_id, data)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(
    article_id: int,
    caller: User = Depends(get_current_user),
    use_case: DeleteArticle = Depends(get_delete_article),
) -> Response:
    """Elimina definitivamente el articulo (autor o admin; 403 si es ajeno)."""
    use_case.execute(caller, article_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
