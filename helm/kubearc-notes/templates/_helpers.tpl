{{/* Labels every object gets */}}
{{- define "notes.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/* Labels the app's Service selects on */}}
{{- define "notes.selectorLabels" -}}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: web
{{- end }}

{{/* Labels Postgres' Service selects on */}}
{{- define "notes.dbSelectorLabels" -}}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: db
{{- end }}

{{/* Name of the Secret holding POSTGRES_PASSWORD: your own (existingSecret) or the chart's */}}
{{- define "notes.dbSecretName" -}}
{{- .Values.postgres.existingSecret | default (printf "%s-postgres" .Release.Name) -}}
{{- end }}
