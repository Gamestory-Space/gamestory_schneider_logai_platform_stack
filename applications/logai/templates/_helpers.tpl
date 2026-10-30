{{- define "logai.host" -}}
{{- $host := index .root.Values.hosts .name -}}
{{- required (printf "hosts.%s is cluster-specific and must be set in values-<cluster>.yaml" .name) $host -}}
{{- end }}

{{- define "logai.url" -}}
https://{{ include "logai.host" . }}
{{- end }}

{{- define "logai.image" -}}
{{- if .digest -}}
{{ .repository }}:{{ .tag }}@{{ .digest }}
{{- else -}}
{{ .repository }}:{{ .tag }}
{{- end -}}
{{- end }}

{{- define "logai.imagePullSecrets" -}}
{{- with .Values.imagePullSecret }}
imagePullSecrets:
  - name: {{ . }}
{{- end }}
{{- end }}

{{/* Pod-level hardening. Takes the uid/gid map from .Values.securityContext. */}}
{{- define "logai.podSecurityContext" -}}
securityContext:
  runAsNonRoot: true
  runAsUser: {{ .runAsUser }}
  runAsGroup: {{ .runAsGroup }}
  fsGroup: {{ .runAsGroup }}
  seccompProfile:
    type: RuntimeDefault
{{- end }}

{{- define "logai.containerSecurityContext" -}}
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
{{- end }}

{{/* Spread replicas across nodes so one Auto Mode node rotation never takes a component down. */}}
{{- define "logai.spread" -}}
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        app: {{ . }}
{{- end }}
