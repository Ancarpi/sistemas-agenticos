# Runbook template — short form

> Origen: A·G.3. Copy this file, do not edit it in place. One runbook per
> service (`production-checklist.yaml`, `obs.runbooks`). Add the step DORA
> requires and this template does not have: **¿esto es notificable?** — initial
> notification of a major incident runs four hours from classifying it as
> major and never more than twenty-four from becoming aware (16.4), and that
> detection timestamp is an event of the Art. 12 register, not an entry in your
> observability tool (16.6).

```text
Servicio:
Owner:
SLO afectado:
Síntomas:
Primeras 5 acciones:
Rollback:
Cómo bloquear herramientas:
Cómo cambiar modelo fallback:
Cómo extraer casos para eval:
Comunicación interna/externa:
Post-mortem owner y fecha:
```
