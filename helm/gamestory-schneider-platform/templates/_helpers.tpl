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
{{- define "schneider.dbSecretName" -}}{{- if .Values.externalDatabase.enabled -}}{{ required "externalDatabase.existingSecret is required" .Values.externalDatabase.existingSecret }}{{- else if .Values.postgres.existingSecret -}}{{ .Values.postgres.existingSecret }}{{- else -}}{{ include "schneider.name" . }}-postgres{{- end -}}{{- end }}
{{- define "schneider.adminSecretName" -}}{{- if .Values.keycloak.existingAdminSecret -}}{{ .Values.keycloak.existingAdminSecret }}{{- else -}}{{ include "schneider.name" . }}-keycloak-admin{{- end -}}{{- end }}
