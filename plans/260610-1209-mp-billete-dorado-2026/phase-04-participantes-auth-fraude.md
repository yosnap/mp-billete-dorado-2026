# Phase-04: Participantes, Auth y Fraude

## Overview
- **Prioridad:** High
- **Estado:** completed
- **Agente:** `backend-specialist`
- **Dependencias:** phase-02
- **Estimación:** 3-4 días

## Descripción
Implementar los bounded contexts `participants` y `fraud`: registro de participantes con consentimiento RGPD, sesión segura, detección de comportamiento anómalo (bots, IPs abusivas, uso masivo de códigos), y panel de auditoría para Marketing.

## Contexto
- [Phase-02](./phase-02-dominio-codigos.md) — `participation_id` se vincula al participante
- [Informe Astro 6.4](../reports/astro-6-research-report.md) — sección 5.3 (CORS y cookies httpOnly)

## Requisitos
### Funcionales
- [x] Modelo `Participant`: `id`, `full_name`, `email` (encriptado), `phone`, `code_id` (FK→codes), `consent_legal`, `consent_marketing`, `ip_address`, `user_agent`, `created_at` *(Nota: modelo unificado sin `Participation` separado; `code_id` sirve como participation_id)*
- [x] Modelo `FraudEvent`: `id`, `ip_address`, `event_type`, `detail` (JSONB), `created_at` *(en lugar de FraudFlag — sin campo severity, no vinculado a participation_id)*
- [x] Endpoint `POST /api/v1/participants/register` — registro con validación RGPD
- [x] Endpoint `GET /api/v1/admin/fraud/flags` — listado de eventos de fraude
- [ ] Endpoint `POST /api/v1/admin/fraud/invalidate/{participation_id}` — anular participación *(no implementado en esta fase)*
- [x] Detección automática de: misma IP > 3 participaciones, user-agent de bot conocido, velocidad anómala de envío

### No Funcionales
- [ ] Email único por participante *(no implementado — constraint UNIQUE pendiente en fase 08)*
- [x] Registro de IP obligatorio en toda participación
- [x] Consentimiento legal requerido para completar registro (consent_legal = true)
- [x] Datos personales encriptados en reposo (pgcrypto + encode base64 para VARCHAR)

## Arquitectura
```
POST /participants/register
  → validar campos obligatorios (Pydantic)
  → verificar consent_legal = true (obligatorio)
  → FraudDetector.check(ip, email, user_agent)
    → si fraud_score > umbral: FraudFlag + continuar (no bloquear, solo marcar)
  → INSERT Participant (email encriptado)
  → INSERT Participation vinculada a code_id
  → return {participant_id, participation_id}
```

## Archivos Relacionados
### Crear
- `backend/app/domains/participants/models.py` — `Participant`, `Participation`
- `backend/app/domains/participants/schemas.py` — schemas con validación Pydantic
- `backend/app/domains/participants/service.py` — lógica de registro
- `backend/app/domains/fraud/models.py` — `FraudFlag`
- `backend/app/domains/fraud/detector.py` — reglas de detección automática
- `backend/app/domains/fraud/router.py` — endpoints admin de fraude
- `backend/alembic/versions/003_participants_fraud_domain.py` — migración

## Pasos de Implementación
1. Crear modelos `Participant`, `Participation` y `FraudFlag` con relaciones
2. Migración Alembic con índices en `email` (encriptado) e `ip_address`
3. Implementar `FraudDetector` con reglas: IP abuse, bot UA, velocidad anómala
4. Implementar `ParticipantService.register()` con llamada al detector
5. Configurar pgcrypto para encriptación de email en reposo
6. Crear endpoints admin con paginación para listado de flags
7. Test: registro válido, registro sin consentimiento (debe fallar), detección de IP abusiva

## Todo List
- [x] Modelos y migración aplicados
- [x] `POST /register` rechaza consent_legal=false con 422 — verificado en vivo
- [x] Email almacenado encriptado en BD (base64(pgp_sym_encrypt)) — verificado en vivo
- [x] FraudDetector marca IP con > 3 participaciones — lógica implementada y probada
- [x] Panel admin lista flags (`GET /api/v1/admin/fraud/flags`) — endpoint disponible
- [ ] Endpoint de invalidación marca participación como anulada — pendiente F07

## Criterios de Éxito
- [x] Registro sin consentimiento legal → 422 Unprocessable Entity — verificado en vivo
- [x] IP con 4 participaciones → FraudEvent creado automáticamente — implementado
- [x] Email no legible en texto plano en PostgreSQL — encriptado base64+pgcrypto
- [ ] Admin puede invalidar participación fraudulenta en < 3 clicks — pendiente F07

## Riesgos
| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| RGPD: retención de datos post-campaña no definida | Alta | Definir con MP antes de go-live; implementar script de purga |
| Falsos positivos en detección de fraude (familia con misma IP) | Media | Fraud es solo flag, no bloqueo automático; revisión manual |
| Email duplicado con encriptación (mismo email = diferente hash) | Media | Usar encriptación determinista (pgcrypto `encrypt`) no hash |

## Consideraciones de Seguridad
- `consent_legal` obligatorio y no modificable post-registro
- IP registrada en cada participación (informado en bases legales)
- Datos personales: solo accesibles por admin autenticado
- Política de retención: a definir con MP (recomendado: purgar 6 meses post-campaña)
- Nunca devolver email en claro en respuestas de API pública

## Próximos Pasos
- Phase-05: notificaciones usan `participant.email` (desencriptado server-side)
- Phase-07: panel admin muestra listado de fraude
