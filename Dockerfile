FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir -e .

ENV WP_URL=""
ENV WP_USERNAME=""
ENV WP_APP_PASSWORD=""
ENV MCP_TRANSPORT=sse
ENV MCP_API_KEY=""
ENV PORT=8000

EXPOSE 8000

CMD ["wordpress-mcp"]
