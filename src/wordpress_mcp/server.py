"""WordPress MCP Server – MCP-Tools für WordPress via REST API."""

import base64
import json
import logging
import os
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)

from .client import wp_request, wp_upload_media  # noqa: E402

server = Server(
    "wordpress-mcp",
    instructions=(
        "MCP-Server für WordPress (REST API v2).\n\n"
        "Hinweise:\n"
        "- Posts und Pages haben denselben Aufbau – nutze die passenden Tools je nach Inhaltstyp.\n"
        "- SEO-Metadaten (Yoast/RankMath) werden über wp_update_seo_meta gesetzt.\n"
        "- Medien-Upload: Dateiinhalt als base64 übergeben, ähnlich wie bei anderen Upload-Tools.\n"
        "- Plugins/Themes abfragen erfordert Admin-Rechte im WordPress.\n"
        "- Status-Werte für Posts/Pages: 'publish', 'draft', 'pending', 'private', 'trash'."
    ),
)


# ---------------------------------------------------------------------------
# Tool-Definitionen
# ---------------------------------------------------------------------------


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # ── Posts ──────────────────────────────────────────────────────────
        types.Tool(
            name="wp_list_posts",
            description="Listet WordPress-Posts. Optional: Status, Suche, Kategorie, Tag, Anzahl, Seite.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "publish|draft|pending|private|trash (Standard: publish)"},
                    "search": {"type": "string"},
                    "categories": {"type": "array", "items": {"type": "integer"}, "description": "Kategorie-IDs"},
                    "tags": {"type": "array", "items": {"type": "integer"}, "description": "Tag-IDs"},
                    "per_page": {"type": "integer", "default": 20},
                    "page": {"type": "integer", "default": 1},
                    "orderby": {"type": "string", "default": "date", "description": "date|title|modified|id"},
                    "order": {"type": "string", "default": "desc", "description": "asc|desc"},
                },
            },
        ),
        types.Tool(
            name="wp_get_post",
            description="Ruft einen einzelnen WordPress-Post anhand seiner ID ab.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="wp_create_post",
            description="Erstellt einen neuen WordPress-Post.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string", "description": "HTML-Inhalt"},
                    "excerpt": {"type": "string"},
                    "status": {"type": "string", "default": "draft", "description": "publish|draft|pending|private"},
                    "categories": {"type": "array", "items": {"type": "integer"}},
                    "tags": {"type": "array", "items": {"type": "integer"}},
                    "featured_media": {"type": "integer", "description": "ID des Titelbilds"},
                    "slug": {"type": "string"},
                },
                "required": ["title"],
            },
        ),
        types.Tool(
            name="wp_update_post",
            description="Aktualisiert einen bestehenden WordPress-Post.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "excerpt": {"type": "string"},
                    "status": {"type": "string"},
                    "categories": {"type": "array", "items": {"type": "integer"}},
                    "tags": {"type": "array", "items": {"type": "integer"}},
                    "featured_media": {"type": "integer"},
                    "slug": {"type": "string"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="wp_delete_post",
            description="Löscht einen WordPress-Post (in den Papierkorb oder endgültig).",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "force": {"type": "boolean", "default": False, "description": "True = endgültig löschen"},
                },
                "required": ["id"],
            },
        ),
        # ── Pages ──────────────────────────────────────────────────────────
        types.Tool(
            name="wp_list_pages",
            description="Listet WordPress-Seiten.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "default": "publish"},
                    "search": {"type": "string"},
                    "per_page": {"type": "integer", "default": 20},
                    "page": {"type": "integer", "default": 1},
                    "parent": {"type": "integer", "description": "ID der übergeordneten Seite"},
                    "orderby": {"type": "string", "default": "menu_order"},
                    "order": {"type": "string", "default": "asc"},
                },
            },
        ),
        types.Tool(
            name="wp_get_page",
            description="Ruft eine einzelne WordPress-Seite anhand ihrer ID ab.",
            inputSchema={
                "type": "object",
                "properties": {"id": {"type": "integer"}},
                "required": ["id"],
            },
        ),
        types.Tool(
            name="wp_create_page",
            description="Erstellt eine neue WordPress-Seite.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "excerpt": {"type": "string"},
                    "status": {"type": "string", "default": "draft"},
                    "parent": {"type": "integer"},
                    "featured_media": {"type": "integer"},
                    "slug": {"type": "string"},
                    "menu_order": {"type": "integer"},
                },
                "required": ["title"],
            },
        ),
        types.Tool(
            name="wp_update_page",
            description="Aktualisiert eine bestehende WordPress-Seite.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "excerpt": {"type": "string"},
                    "status": {"type": "string"},
                    "parent": {"type": "integer"},
                    "featured_media": {"type": "integer"},
                    "slug": {"type": "string"},
                    "menu_order": {"type": "integer"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="wp_delete_page",
            description="Löscht eine WordPress-Seite.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "force": {"type": "boolean", "default": False},
                },
                "required": ["id"],
            },
        ),
        # ── Kategorien ─────────────────────────────────────────────────────
        types.Tool(
            name="wp_list_categories",
            description="Listet alle WordPress-Kategorien.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string"},
                    "per_page": {"type": "integer", "default": 100},
                    "hide_empty": {"type": "boolean", "default": False},
                },
            },
        ),
        types.Tool(
            name="wp_create_category",
            description="Erstellt eine neue WordPress-Kategorie.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "slug": {"type": "string"},
                    "parent": {"type": "integer"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="wp_update_category",
            description="Aktualisiert eine bestehende WordPress-Kategorie.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "slug": {"type": "string"},
                    "parent": {"type": "integer"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="wp_delete_category",
            description="Löscht eine WordPress-Kategorie.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "force": {"type": "boolean", "default": True},
                },
                "required": ["id"],
            },
        ),
        # ── Tags ───────────────────────────────────────────────────────────
        types.Tool(
            name="wp_list_tags",
            description="Listet alle WordPress-Tags.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string"},
                    "per_page": {"type": "integer", "default": 100},
                    "hide_empty": {"type": "boolean", "default": False},
                },
            },
        ),
        types.Tool(
            name="wp_create_tag",
            description="Erstellt einen neuen WordPress-Tag.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "slug": {"type": "string"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="wp_update_tag",
            description="Aktualisiert einen bestehenden WordPress-Tag.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "slug": {"type": "string"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="wp_delete_tag",
            description="Löscht einen WordPress-Tag.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "force": {"type": "boolean", "default": True},
                },
                "required": ["id"],
            },
        ),
        # ── Medien ─────────────────────────────────────────────────────────
        types.Tool(
            name="wp_list_media",
            description="Listet Medien in der WordPress-Mediathek.",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string"},
                    "media_type": {"type": "string", "description": "image|video|audio|application"},
                    "mime_type": {"type": "string", "description": "z.B. image/jpeg"},
                    "per_page": {"type": "integer", "default": 20},
                    "page": {"type": "integer", "default": 1},
                },
            },
        ),
        types.Tool(
            name="wp_upload_media",
            description="Lädt eine Datei in die WordPress-Mediathek hoch. Dateiinhalt als base64.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Dateiname mit Erweiterung, z.B. 'bild.jpg'"},
                    "content_type": {"type": "string", "description": "MIME-Typ, z.B. 'image/jpeg'"},
                    "data_base64": {"type": "string", "description": "Dateiinhalt als base64-kodierter String"},
                    "title": {"type": "string", "description": "Titel in der Mediathek (optional)"},
                    "alt_text": {"type": "string", "description": "Alt-Text für Barrierefreiheit (optional)"},
                },
                "required": ["filename", "content_type", "data_base64"],
            },
        ),
        types.Tool(
            name="wp_update_media",
            description="Aktualisiert Metadaten eines Medienelements (Titel, Alt-Text, Beschreibung).",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "string"},
                    "alt_text": {"type": "string"},
                    "caption": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["id"],
            },
        ),
        types.Tool(
            name="wp_delete_media",
            description="Löscht ein Medienelement aus der WordPress-Mediathek.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "force": {"type": "boolean", "default": True},
                },
                "required": ["id"],
            },
        ),
        # ── SEO ────────────────────────────────────────────────────────────
        types.Tool(
            name="wp_update_seo_meta",
            description=(
                "Setzt SEO-Metadaten für einen Post oder eine Seite. "
                "Unterstützt All in One SEO (AIOSEO), Yoast SEO und RankMath. "
                "AIOSEO ist das aktive Plugin auf dieser WordPress-Installation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "Post- oder Seiten-ID"},
                    "post_type": {"type": "string", "default": "posts", "description": "posts|pages"},
                    "seo_title": {"type": "string", "description": "SEO-Titel (Meta Title)"},
                    "seo_description": {"type": "string", "description": "Meta Description"},
                    "focus_keyword": {"type": "string", "description": "Fokus-Keyword (kommagetrennt bei mehreren)"},
                    "og_title": {"type": "string", "description": "Open Graph Titel (Social Media)"},
                    "og_description": {"type": "string", "description": "Open Graph Beschreibung"},
                    "canonical_url": {"type": "string", "description": "Kanonische URL"},
                    "noindex": {"type": "boolean", "description": "Seite aus Suchindex ausschließen"},
                },
                "required": ["id"],
            },
        ),
        # ── Site / System ──────────────────────────────────────────────────
        types.Tool(
            name="wp_get_site_info",
            description="Gibt allgemeine Informationen zur WordPress-Installation zurück (Name, URL, Beschreibung, Version).",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="wp_list_plugins",
            description="Listet installierte WordPress-Plugins mit Status. Erfordert Admin-Rechte.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "active|inactive (leer = alle)"},
                },
            },
        ),
        types.Tool(
            name="wp_list_themes",
            description="Listet installierte WordPress-Themes. Erfordert Admin-Rechte.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ---------------------------------------------------------------------------
# Tool-Handler
# ---------------------------------------------------------------------------


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    try:
        result = await _dispatch(name, arguments)
    except Exception as exc:
        result = {"error": str(exc)}
    return [
        types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))
    ]


async def _dispatch(name: str, args: dict[str, Any]) -> Any:
    # Posts
    if name == "wp_list_posts":
        return await _list_content("posts", args)
    if name == "wp_get_post":
        return await wp_request("GET", f"posts/{args['id']}")
    if name == "wp_create_post":
        return await wp_request("POST", "posts", json_data=_post_payload(args))
    if name == "wp_update_post":
        return await wp_request("POST", f"posts/{args['id']}", json_data=_post_payload(args))
    if name == "wp_delete_post":
        return await wp_request("DELETE", f"posts/{args['id']}", params={"force": args.get("force", False)})

    # Pages
    if name == "wp_list_pages":
        return await _list_content("pages", args)
    if name == "wp_get_page":
        return await wp_request("GET", f"pages/{args['id']}")
    if name == "wp_create_page":
        return await wp_request("POST", "pages", json_data=_page_payload(args))
    if name == "wp_update_page":
        return await wp_request("POST", f"pages/{args['id']}", json_data=_page_payload(args))
    if name == "wp_delete_page":
        return await wp_request("DELETE", f"pages/{args['id']}", params={"force": args.get("force", False)})

    # Categories
    if name == "wp_list_categories":
        return await wp_request("GET", "categories", params=_filter_none({
            "search": args.get("search"),
            "per_page": args.get("per_page", 100),
            "hide_empty": args.get("hide_empty", False),
        }))
    if name == "wp_create_category":
        return await wp_request("POST", "categories", json_data=_taxonomy_payload(args))
    if name == "wp_update_category":
        return await wp_request("POST", f"categories/{args['id']}", json_data=_taxonomy_payload(args))
    if name == "wp_delete_category":
        return await wp_request("DELETE", f"categories/{args['id']}", params={"force": args.get("force", True)})

    # Tags
    if name == "wp_list_tags":
        return await wp_request("GET", "tags", params=_filter_none({
            "search": args.get("search"),
            "per_page": args.get("per_page", 100),
            "hide_empty": args.get("hide_empty", False),
        }))
    if name == "wp_create_tag":
        return await wp_request("POST", "tags", json_data=_taxonomy_payload(args))
    if name == "wp_update_tag":
        return await wp_request("POST", f"tags/{args['id']}", json_data=_taxonomy_payload(args))
    if name == "wp_delete_tag":
        return await wp_request("DELETE", f"tags/{args['id']}", params={"force": args.get("force", True)})

    # Media
    if name == "wp_list_media":
        return await wp_request("GET", "media", params=_filter_none({
            "search": args.get("search"),
            "media_type": args.get("media_type"),
            "mime_type": args.get("mime_type"),
            "per_page": args.get("per_page", 20),
            "page": args.get("page", 1),
        }))
    if name == "wp_upload_media":
        file_data = base64.b64decode(args["data_base64"])
        return await wp_upload_media(
            filename=args["filename"],
            content_type=args["content_type"],
            file_data=file_data,
            title=args.get("title"),
            alt_text=args.get("alt_text"),
        )
    if name == "wp_update_media":
        return await wp_request("POST", f"media/{args['id']}", json_data=_filter_none({
            "title": args.get("title"),
            "alt_text": args.get("alt_text"),
            "caption": args.get("caption"),
            "description": args.get("description"),
        }))
    if name == "wp_delete_media":
        return await wp_request("DELETE", f"media/{args['id']}", params={"force": args.get("force", True)})

    # SEO
    if name == "wp_update_seo_meta":
        return await _update_seo_meta(args)

    # Site / System
    if name == "wp_get_site_info":
        return await wp_request("GET", "settings")
    if name == "wp_list_plugins":
        params = {}
        if args.get("status"):
            params["status"] = args["status"]
        return await wp_request("GET", "plugins", params=params or None)
    if name == "wp_list_themes":
        return await wp_request("GET", "themes")

    raise ValueError(f"Unbekanntes Tool: {name}")


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _filter_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _post_payload(args: dict[str, Any]) -> dict[str, Any]:
    fields = ["title", "content", "excerpt", "status", "categories", "tags", "featured_media", "slug"]
    return _filter_none({f: args[f] for f in fields if f in args and f != "id"})


def _page_payload(args: dict[str, Any]) -> dict[str, Any]:
    fields = ["title", "content", "excerpt", "status", "parent", "featured_media", "slug", "menu_order"]
    return _filter_none({f: args[f] for f in fields if f in args and f != "id"})


def _taxonomy_payload(args: dict[str, Any]) -> dict[str, Any]:
    fields = ["name", "description", "slug", "parent"]
    return _filter_none({f: args[f] for f in fields if f in args and f != "id"})


async def _list_content(post_type: str, args: dict[str, Any]) -> Any:
    params = _filter_none({
        "status": args.get("status", "publish"),
        "search": args.get("search"),
        "categories": ",".join(str(c) for c in args["categories"]) if args.get("categories") else None,
        "tags": ",".join(str(t) for t in args["tags"]) if args.get("tags") else None,
        "per_page": args.get("per_page", 20),
        "page": args.get("page", 1),
        "orderby": args.get("orderby", "date"),
        "order": args.get("order", "desc"),
        "parent": args.get("parent"),
    })
    return await wp_request("GET", post_type, params=params)


async def _update_seo_meta(args: dict[str, Any]) -> dict[str, Any]:
    post_id = args["id"]
    post_type = args.get("post_type", "posts")

    # AIOSEO (active on energieberatung-odenwaldkreis.de), Yoast und RankMath parallel setzen
    meta: dict[str, Any] = {}

    if args.get("seo_title"):
        meta["_aioseo_title"] = args["seo_title"]
        meta["_yoast_wpseo_title"] = args["seo_title"]
        meta["rank_math_title"] = args["seo_title"]
    if args.get("seo_description"):
        meta["_aioseo_description"] = args["seo_description"]
        meta["_yoast_wpseo_metadesc"] = args["seo_description"]
        meta["rank_math_description"] = args["seo_description"]
    if args.get("focus_keyword"):
        meta["_aioseo_keywords"] = args["focus_keyword"]
        meta["_yoast_wpseo_focuskw"] = args["focus_keyword"]
        meta["rank_math_focus_keyword"] = args["focus_keyword"]
    if args.get("og_title"):
        meta["_aioseo_og_title"] = args["og_title"]
    if args.get("og_description"):
        meta["_aioseo_og_description"] = args["og_description"]
    if args.get("canonical_url"):
        meta["_aioseo_canonical_url"] = args["canonical_url"]
        meta["_yoast_wpseo_canonical"] = args["canonical_url"]
    if args.get("noindex") is not None:
        noindex = args["noindex"]
        meta["_aioseo_robots_noindex"] = "1" if noindex else "0"
        meta["_yoast_wpseo_meta-robots-noindex"] = "1" if noindex else "0"
        meta["rank_math_robots"] = ["noindex"] if noindex else []

    if not meta:
        return {"error": "Keine SEO-Felder angegeben."}

    return await wp_request("POST", f"{post_type}/{post_id}", json_data={"meta": meta})


# ---------------------------------------------------------------------------
# Einstiegspunkt
# ---------------------------------------------------------------------------


def main() -> None:
    import asyncio

    if os.getenv("MCP_TRANSPORT", "stdio") == "sse":
        _run_sse()
    else:
        asyncio.run(mcp.server.stdio.run_server(server))


def _run_sse() -> None:
    import contextlib
    from collections.abc import AsyncIterator

    import httpx as _httpx
    import uvicorn
    from mcp.server.sse import SseServerTransport
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import Mount, Route

    mcp_api_key = os.getenv("MCP_API_KEY", "")
    oidc_introspection_url = os.getenv("OIDC_INTROSPECTION_URL", "")
    oidc_client_id = os.getenv("OIDC_CLIENT_ID", "")
    oidc_client_secret = os.getenv("OIDC_CLIENT_SECRET", "")

    async def _is_authorized(request: Request) -> tuple[bool, str | None]:
        logging.debug("Auth-Check: %s %s", request.method, request.url.path)
        if not mcp_api_key:
            return True, None

        auth = request.headers.get("Authorization", "")
        if not auth:
            return False, "no_header"
        if auth == f"Bearer {mcp_api_key}":
            logging.info("Auth OK: statischer Bearer Token")
            return True, None
        if not auth.startswith("Bearer "):
            return False, "invalid_token"

        if oidc_introspection_url and oidc_client_id and oidc_client_secret:
            jwt_token = auth[7:]
            try:
                async with _httpx.AsyncClient() as http:
                    resp = await http.post(
                        oidc_introspection_url,
                        data={"token": jwt_token},
                        auth=(oidc_client_id, oidc_client_secret),
                        timeout=5.0,
                    )
                    active = resp.json().get("active", False)
                    logging.info("Introspection: HTTP %s, active=%s", resp.status_code, active)
                    return (True, None) if active else (False, "invalid_token")
            except Exception as e:
                logging.error("Introspection fehlgeschlagen: %s", e)
                return False, "invalid_token"

        return False, "invalid_token"

    def _unauthorized(reason: str | None) -> Response:
        if reason == "invalid_token":
            www = (
                'Bearer realm="wordpress-mcp", error="invalid_token", '
                'error_description="The access token expired or is invalid"'
            )
            return Response("Unauthorized", status_code=401, headers={"WWW-Authenticate": www})
        return Response("Unauthorized", status_code=401)

    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request):
        ok, reason = await _is_authorized(request)
        if not ok:
            return _unauthorized(reason)
        logging.info("SSE-Verbindung akzeptiert")
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())
        return Response()

    class _AlreadySent(Response):
        def __init__(self) -> None:
            super().__init__(content=b"", status_code=200)

        async def __call__(self, scope, receive, send):
            return

    session_manager = StreamableHTTPSessionManager(app=server, json_response=True)

    async def handle_streamable_http(request: Request):
        ok, reason = await _is_authorized(request)
        if not ok:
            return _unauthorized(reason)
        await session_manager.handle_request(request.scope, request.receive, request._send)
        return _AlreadySent()

    @contextlib.asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logging.info("StreamableHTTPSessionManager gestartet")
            yield

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_streamable_http, methods=["POST"]),
            Route("/mcp", endpoint=handle_streamable_http, methods=["POST"]),
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        lifespan=lifespan,
    )

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
