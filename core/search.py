"""Cerca unificada JMEJCat (v4.0).

Helper compartit per notes i tramitació:
- escape_like(): escapa %, _ i \\ per a LIKE literal amb ESCAPE '\\'.
- build_like_condition(): genera "col LIKE ? ESCAPE '\\'" + param.
"""

from typing import Any


def escape_like(query: str) -> str:
    """Escapa %, _ i \\ perquè es busquin literalment en un LIKE."""
    return query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def like_param(query: str) -> str:
    """Retorna %query_escapada% per a LIKE parcial."""
    return f"%{escape_like(query)}%"


def build_like_condition(column: str, query: str) -> tuple[str, Any]:
    """Retorna (condició SQL, paràmetre) per a cerca parcial literal.

    Exemple: build_like_condition("title", "a%b") ->
        ("title LIKE ? ESCAPE '\\\\'", "%a\\%b%")
    """
    return f"{column} LIKE ? ESCAPE '\\'", like_param(query)
