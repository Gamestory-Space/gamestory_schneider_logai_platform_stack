FROM scratch
ARG BUNDLE_VERSION=dev
LABEL org.opencontainers.image.title="Schneider LogAI deployment bundle" \
      org.opencontainers.image.description="Client-only Compose and Helm deployment assets" \
      org.opencontainers.image.version="${BUNDLE_VERSION}" \
      org.opencontainers.image.vendor="Gamestory"
COPY compose.yaml /bundle/compose.yaml
COPY helm/gamestory-schneider-platform /bundle/helm/gamestory-schneider-platform
COPY environments/client-local /bundle/environments/client-local
COPY environments/uat /bundle/environments/uat
COPY environments/prod /bundle/environments/prod
COPY scripts/client /bundle/scripts
COPY scripts/smoke-test.sh /bundle/scripts/smoke-test.sh
COPY docs/client-local.md /bundle/docs/client-local.md
COPY docs/schneider-handoff.md /bundle/docs/schneider-handoff.md
COPY docs/deployment-model.md /bundle/docs/deployment-model.md
COPY identity/schneider.identity.env.example /bundle/identity/schneider.identity.env.example
COPY README.client.md /bundle/README.md
CMD ["/bundle/README.md"]
