FROM python:3.13-slim-bookworm AS build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY services/requirements.lock ./requirements.lock
RUN python -m venv /opt/venv && /opt/venv/bin/pip install -r requirements.lock

FROM python:3.13-slim-bookworm AS runtime
ARG BUILD_COMMIT=unknown
LABEL org.opencontainers.image.title="audit-svc" org.opencontainers.image.version="1.0.0" org.opencontainers.image.revision=$BUILD_COMMIT
ENV PATH=/opt/venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 CONTRACT_DIR=/app/contracts
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY services/audit_svc ./audit_svc
COPY services/tests/test_audit.py ./tests/test_audit.py
COPY services/tools ./tools
COPY contracts/*.yaml ./contracts/
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=3)"
CMD ["uvicorn", "audit_svc.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--log-level", "warning"]
