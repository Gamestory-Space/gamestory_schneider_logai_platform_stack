{{- define "schneider.name" -}}{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}{{- end }}
{{- define "schneider.labels" -}}
app.kubernetes.io/part-of: gamestory-schneider-platform
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | quote }}
{{- end }}
{{- define "schneider.selectorLabels" -}}
app.kubernetes.io/name: {{ include "schneider.name" .root }}-{{ .component }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
{{- end }}
{{- define "schneider.image" -}}{{- if .digest -}}{{ printf "%s@%s" .repository .digest }}{{- else -}}{{ printf "%s:%s" .repository .tag }}{{- end -}}{{- end }}
{{- define "schneider.dbSecretName" -}}{{- if .Values.externalDatabase.enabled -}}{{ required "externalDatabase.existingSecret is required" .Values.externalDatabase.existingSecret }}{{- else -}}{{ required "postgres.existingSecret is required; supply a runtime database Secret" .Values.postgres.existingSecret }}{{- end -}}{{- end }}
{{- define "schneider.adminSecretName" -}}{{ required "keycloak.existingAdminSecret is required; supply a runtime admin Secret" .Values.keycloak.existingAdminSecret }}{{- end }}
{{- define "schneider.uiUrl" -}}
{{- if .Values.identity.publicUiUrl -}}{{ .Values.identity.publicUiUrl | trimSuffix "/" }}{{- else if has .Values.global.environment (list "client-local" "build" "release") -}}http://localhost:3000{{- else -}}{{ printf "https://logai-%s.%s" .Values.global.environment .Values.identity.domain }}{{- end -}}
{{- end }}
{{- define "schneider.keycloakUrl" -}}
{{- if .Values.identity.publicUrl -}}{{ .Values.identity.publicUrl | trimSuffix "/" }}{{- else if has .Values.global.environment (list "client-local" "build" "release") -}}http://localhost:8080{{- else -}}{{ printf "https://keycloak-%s.%s" .Values.global.environment .Values.identity.domain }}{{- end -}}
{{- end }}
{{- define "schneider.apiUrl" -}}
{{- if .Values.identity.logaiApiUrl -}}{{ .Values.identity.logaiApiUrl | trimSuffix "/" }}{{- else if has .Values.global.environment (list "client-local" "build" "release") -}}http://localhost:8010{{- else -}}{{ printf "https://api-%s.%s" .Values.global.environment .Values.identity.domain }}{{- end -}}
{{- end }}
{{- define "schneider.identityApiUrl" -}}
{{- if .Values.identity.identityApiUrl -}}{{ .Values.identity.identityApiUrl | trimSuffix "/" }}{{- else if has .Values.global.environment (list "client-local" "build" "release") -}}http://localhost:8000{{- else -}}{{ printf "https://identity-%s.%s" .Values.global.environment .Values.identity.domain }}{{- end -}}
{{- end }}
{{- define "schneider.internalKeycloakUrl" -}}{{ default (printf "http://%s-keycloak.%s.svc:8080" (include "schneider.name" .) .Release.Namespace) .Values.identity.internalUrl }}{{- end }}
