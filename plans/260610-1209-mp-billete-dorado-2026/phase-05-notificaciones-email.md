# Phase-05: Notificaciones y Email Automation

## Overview
- **Prioridad:** High
- **Estado:** pending
- **Agente:** `backend-specialist`
- **Dependencias:** phase-03, phase-04
- **Estimación:** 3-4 días

## Descripción
Implementar el bounded context `notifications`: los 9 tipos de email automatizados de la campaña, workers Celery para envío async, plantillas HTML responsive y triggers por evento (spin completado, días dorados, gran final).

## Contexto
- [Phase-03](./phase-03-motor-ruleta-premios.md) — evento `spin_completed` dispara emails
- [Phase-04](./phase-04-participantes-auth-fraude.md) — `participant.email` (desencriptado server-side)
- 9 tipos de email definidos en el plan de campaña

## Requisitos
### Funcionales
- [ ] Los 9 tipos de email implementados como plantillas HTML:
  1. `welcome` — bienvenida al registrarse
  2. `winner` — ganador con instrucciones de recogida de premio
  3. `no_prize` — participante sin premio con ánimo
  4. `golden_days` — días dorados MP (campaña especial)
  5. `new_prizes_unlocked` — activación de nuevos premios (fase)
  6. `last_chance` — última oportunidad antes del cierre
  7. `grand_final` — gran final MP Billete Dorado
  8. `instant_winner_sms` — mensaje inmediato ganador (opcional SMS)
  9. `instant_no_prize_sms` — mensaje inmediato no ganador (opcional SMS)
- [ ] Modelo `EmailLog`: `id`, `participant_id`, `type`, `status`, `sent_at`, `error`
- [ ] Endpoint `POST /api/v1/admin/notifications/send` — envío manual de campaña
- [ ] Worker Celery para envío async con retry en caso de fallo

### No Funcionales
- [ ] Proveedor SMTP: SendGrid o AWS SES (configurable por env var)
- [ ] SPF, DKIM y DMARC configurados en dominio `mainpaper.com`
- [ ] Rate limit de envío masivo: máx 100 emails/min para evitar spam filters
- [ ] Plantillas responsive (mobile-first, 600px máx)
- [ ] Unsubscribe link en todos los emails de marketing (RGPD)

## Arquitectura
```
Evento spin_completed
  → Celery task: send_notification.delay(participant_id, type, context)
    → desencriptar email (server-side)
    → renderizar plantilla Jinja2 con contexto
    → enviar via SendGrid API / SMTP
    → INSERT EmailLog (status=sent|failed)
    → si fallo: retry x3 con backoff exponencial

Cron Celery Beat (campañas masivas):
  → golden_days: configurable por admin
  → new_prizes_unlocked: trigger automático al cambiar fase
  → last_chance: 7 días antes del 30-sep-2026
  → grand_final: 30-sep-2026
```

## Archivos Relacionados
### Crear
- `backend/app/domains/notifications/models.py` — `EmailLog`
- `backend/app/domains/notifications/schemas.py` — schemas de envío
- `backend/app/domains/notifications/service.py` — lógica de envío y logging
- `backend/app/domains/notifications/tasks.py` — tareas Celery
- `backend/app/domains/notifications/router.py` — endpoints admin
- `backend/app/domains/notifications/templates/` — plantillas Jinja2 HTML (9 archivos)
- `backend/app/domains/notifications/beat_schedule.py` — cron de Celery Beat
- `backend/alembic/versions/004_notifications_domain.py` — migración

## Pasos de Implementación
1. Crear modelo `EmailLog` y migración
2. Configurar Celery con Redis como broker y result backend
3. Implementar `NotificationService.send()` con Jinja2 + SendGrid client
4. Crear las 9 plantillas HTML (responsive, con unsubscribe link en las de marketing)
5. Implementar tarea Celery `send_notification` con retry x3
6. Configurar Celery Beat con schedule para emails de campaña
7. Crear endpoint admin para envío manual y consulta de logs
8. Test: envío de cada tipo de email a dirección de prueba; verificar recepción y render

## Todo List
- [ ] Celery worker arranca y procesa tareas desde Redis
- [ ] Los 9 tipos de plantilla HTML renderizan correctamente
- [ ] Email de ganador incluye nombre del premio e instrucciones
- [ ] Unsubscribe link funcional en emails de marketing
- [ ] EmailLog registra cada envío con status
- [ ] Retry automático en fallo SMTP (x3, backoff exponencial)
- [ ] Celery Beat programa `last_chance` para 23-sep-2026 y `grand_final` para 30-sep-2026

## Criterios de Éxito
- [ ] Email de ganador llega en < 30s tras completar el spin
- [ ] 0 emails perdidos: todos los fallos en `EmailLog` con motivo
- [ ] Plantillas renderizadas sin errores en Gmail, Outlook y Apple Mail
- [ ] SPF/DKIM validados con herramienta MX Toolbox antes del lanzamiento

## Riesgos
| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Dominio mainpaper.com sin SPF/DKIM → emails en spam | Alta si no se configura | Configurar semana 1; validar con MX Toolbox antes del 15-jun |
| Envío masivo triggerando límites de SendGrid free tier | Media | Contratar plan de pago (35k emails estimados) |
| Email de ganador con datos incorrectos del premio | Baja | Test de integración spin → email antes de go-live |

## Consideraciones de Seguridad
- Email desencriptado solo en memoria del worker, nunca persistido en claro
- Unsubscribe con token firmado (no enumerable)
- Logs de email sin contenido personal (solo participant_id y tipo)
- Credenciales SMTP solo en variables de entorno, nunca en código

## Próximos Pasos
- Phase-08: tests de integración del flujo completo registro → spin → email
