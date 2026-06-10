---
name: backend-specialist
description: Guía de referencia técnica para el agente backend-specialist. Actívala en cualquier tarea de desarrollo backend con Python (FastAPI, Django, Flask), Spring Boot, bases de datos PostgreSQL, MongoDB o Firebase, diseño de APIs REST/GraphQL, autenticación/autorización, microservicios, optimización de performance, o seguridad OWASP. Usar siempre que el contexto involucre backend, APIs, bases de datos o arquitectura de servidor.
---

# Backend Specialist — Guía de Referencia Técnica

## Navegación Rápida

| Necesidad | Sección |
|-----------|---------|
| ¿Python o Spring Boot? | [Selección de Stack](#selección-de-stack) |
| ¿PostgreSQL, MongoDB o Firebase? | [Selección de Base de Datos](#selección-de-base-de-datos) |
| Diseño de API | [Patrones de API](#patrones-de-api) |
| Arquitectura backend | [Patrones Arquitectónicos](#patrones-arquitectónicos) |
| Auth/autorización | [Seguridad y Autenticación](#seguridad-y-autenticación) |
| Optimizar performance | [Performance y Optimización](#performance-y-optimización) |
| Estándares de código | [Estándares de Código](#estándares-de-código) |

---

## Selección de Stack

### Python vs Spring Boot

| Criterio | Python (FastAPI/Django) | Spring Boot |
|----------|------------------------|-------------|
| Velocidad de desarrollo | ✅ Más rápido | ⚠️ Más verboso |
| Ecosistema ML/Data | ✅ Natural | ❌ Limitado |
| Concurrencia async | ✅ FastAPI + asyncio | ✅ WebFlux reactivo |
| Tipado estático | ⚠️ Pydantic + hints | ✅ Java nativo |
| Microservicios maduros | ⚠️ Con esfuerzo | ✅ Spring Cloud |
| Mensajería / Kafka | ⚠️ Celery/aiohttp | ✅ Spring AMQP nativo |

**Regla general:** Python para APIs rápidas, ML/data y startups. Spring Boot para sistemas empresariales, alta concurrencia y ecosistemas Java existentes.

### Frameworks Python

- **FastAPI**: APIs async modernas, validación automática con Pydantic v2, generación de OpenAPI. Primera opción para nuevas APIs.
- **Django + DRF**: Proyectos con admin panel, ORM robusto, autenticación integrada.
- **Flask**: Microservicios simples, prototipos, máxima flexibilidad.

---

## Selección de Base de Datos

| Necesidad | Elegir |
|-----------|--------|
| Transacciones ACID, relaciones complejas | PostgreSQL |
| Esquema flexible, documentos anidados | MongoDB |
| Sincronización real-time, mobile/web | Firebase Realtime DB |
| Datos estructurados + consultas complejas | PostgreSQL + JSONB |
| Búsqueda full-text avanzada | MongoDB Atlas Search |
| Auth + serverless + backend ligero | Firebase Auth + Firestore |
| Alta carga de escritura + sharding | MongoDB |
| Multi-tenancy con row-level security | PostgreSQL |

---

## Patrones de API

### REST — Convenciones
```
GET    /resources          → listar (paginado)
POST   /resources          → crear
GET    /resources/{id}     → obtener uno
PATCH  /resources/{id}     → actualizar parcial
DELETE /resources/{id}     → eliminar
```

**Paginación para datasets grandes:** cursor-based sobre offset (evita drift en datos dinámicos).

### GraphQL — Cuándo usarlo
- Cliente necesita flexibilidad en los campos que consume
- Múltiples clientes (mobile, web) con necesidades distintas
- Reduce over-fetching/under-fetching

### gRPC — Cuándo usarlo
- Comunicación interna entre microservicios
- Contratos estrictos con proto files
- Alta performance, baja latencia

---

## Patrones Arquitectónicos

### Repository Pattern
Abstrae el acceso a datos. El dominio no conoce si el storage es Postgres, Mongo o Firebase.

```python
# Interfaz del dominio
class UserRepository(Protocol):
    async def find_by_id(self, user_id: UUID) -> User | None: ...
    async def save(self, user: User) -> User: ...

# Implementación concreta
class PostgresUserRepository:
    async def find_by_id(self, user_id: UUID) -> User | None:
        row = await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return User.from_row(row) if row else None
```

### Service Layer
Encapsula lógica de negocio. Orquesta repositories, valida reglas de dominio.

```python
class UserService:
    def __init__(self, repo: UserRepository, email_service: EmailService):
        self._repo = repo
        self._email = email_service

    async def register(self, payload: UserCreateSchema) -> UserResponse:
        if await self._repo.find_by_email(payload.email):
            raise ConflictError("Email already registered")
        user = await self._repo.save(User.create(payload))
        await self._email.send_welcome(user.email)
        return UserResponse.from_domain(user)
```

### DTO / Schema Pattern
- **Schema de entrada**: valida y sanitiza (Pydantic / Spring @Valid)
- **Modelo de dominio**: lógica interna
- **Response DTO**: contrato público de la API — nunca exponer el modelo interno

### CQRS — Cuándo aplicarlo
Cuando lecturas y escrituras tienen necesidades muy distintas (alta carga de lectura, escrituras complejas). Separa handlers de Command (escribe) y Query (lee).

### Event-Driven — Cuándo aplicarlo
- Desacoplar servicios que no necesitan respuesta inmediata
- Celery para tareas background en Python
- Kafka / Spring AMQP para mensajería entre microservicios
- Firebase Events para reactividad en tiempo real

---

## Seguridad y Autenticación

### Checklist Siempre Activo
- [ ] Inputs validados y sanitizados antes de cualquier operación
- [ ] Queries parametrizadas (nunca interpolación de strings en SQL/NoSQL)
- [ ] Secrets en variables de entorno, nunca hardcodeados
- [ ] Rate limiting en endpoints públicos
- [ ] CORS configurado explícitamente (no `*` en producción)
- [ ] Datos sensibles encriptados en reposo y en tránsito
- [ ] Logging de eventos de seguridad sin exponer datos sensibles
- [ ] JWT con expiración corta + refresh tokens

### JWT + OAuth2
- **Access token**: vida corta (15min–1h), en memoria del cliente
- **Refresh token**: vida larga, httpOnly cookie o secure storage
- **OAuth2 + PKCE**: para flujos con usuario final
- **Spring Security**: `@PreAuthorize("hasRole('ADMIN')")` para RBAC
- **FastAPI**: `Depends(get_current_user)` en los endpoints protegidos

### Contraseñas
Siempre **Argon2id** (no bcrypt, no MD5, no SHA sin salt). En Python: `argon2-cffi`. En Spring: `PasswordEncoder` de Spring Security.

---

## Performance y Optimización

### Metodología: Medir Antes de Optimizar
1. Identifica el cuello de botella con datos reales
2. `EXPLAIN ANALYZE` en PostgreSQL, `.explain()` en MongoDB
3. Perfila antes de reescribir — el problema raramente está donde se cree

### PostgreSQL — Índices Clave
```sql
-- Alta cardinalidad, búsquedas exactas
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Queries con múltiples condiciones frecuentes
CREATE INDEX idx_orders_user_status ON orders(user_id, status) WHERE deleted_at IS NULL;

-- Búsqueda full-text
CREATE INDEX idx_articles_search ON articles USING GIN(to_tsvector('spanish', title || ' ' || body));

-- JSONB
CREATE INDEX idx_metadata_tags ON products USING GIN(metadata->'tags');
```

**Cuándo NO crear un índice:** tabla pequeña (<10k filas), columna de baja cardinalidad (booleanos, enums con pocas opciones), columna raramente consultada.

### MongoDB — Optimizaciones
```js
// Índice compuesto para query frecuente
db.orders.createIndex({ userId: 1, createdAt: -1 })

// Projection para traer solo campos necesarios
db.users.find({ status: "active" }, { name: 1, email: 1, _id: 0 })

// Aggregation Pipeline en lugar de múltiples queries
db.orders.aggregate([
  { $match: { status: "completed" } },
  { $group: { _id: "$userId", total: { $sum: "$amount" } } },
  { $sort: { total: -1 } },
  { $limit: 10 }
])
```

### Caché con Redis
```python
CACHE_TTL = 300  # 5 minutos

async def get_user(user_id: str) -> User:
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return User.model_validate_json(cached)
    user = await user_repo.find_by_id(user_id)
    await redis.setex(f"user:{user_id}", CACHE_TTL, user.model_dump_json())
    return user
```

### N+1 Queries — Detección y Solución
**Síntoma:** 1 query para listar + N queries para cada ítem relacionado.
**Solución Python/SQLAlchemy:** `selectinload()` o `joinedload()`.
**Solución Spring:** `@EntityGraph` o `JOIN FETCH` en JPQL.
**Solución MongoDB:** `$lookup` en aggregation pipeline.

### Connection Pooling
- **PostgreSQL + Python**: `asyncpg` con pool de 10-20 conexiones, `PgBouncer` para múltiples instancias
- **PostgreSQL + Spring**: HikariCP (default), ajustar `maximum-pool-size` según workload
- **MongoDB**: driver nativo con pool configurable, `maxPoolSize: 50` para alta carga

---

## Firebase — Referencia Rápida

### Firestore — Decisiones de Modelado
- **Embed** datos que siempre se leen juntos (perfil dentro del usuario)
- **Referencia** datos que crecen sin límite o se leen independientemente
- **Subcollections** para relaciones 1:N con queries independientes
- Límite: 1 escritura/segundo por documento — particiona contadores con distributed counters

### Reglas de Seguridad
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    match /public/{document=**} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

### Firebase Admin SDK
```python
import firebase_admin
from firebase_admin import credentials, firestore, auth

app = firebase_admin.initialize_app(credentials.Certificate("service-account.json"))
db = firestore.client()

# Verificar token de usuario
decoded_token = auth.verify_id_token(id_token)
uid = decoded_token['uid']
```

---

## Estándares de Código

### Python — Reglas No Negociables
```python
# Type hints siempre
async def create_order(payload: OrderCreateSchema, user_id: UUID) -> OrderResponse:
    ...

# Errores específicos, no genéricos
try:
    result = await repo.save(entity)
except UniqueViolationError:
    raise HTTPException(409, "Resource already exists")
except DatabaseError as e:
    logger.error("DB error: %s", e, exc_info=True)
    raise HTTPException(500, "Internal server error")

# Logging estructurado, sin datos sensibles
logger.info("User created", extra={"user_id": str(user.id), "email_domain": domain})
```

### Spring Boot — Reglas No Negociables
```java
@Service
@RequiredArgsConstructor
@Slf4j
public class OrderService {
    private final OrderRepository orderRepository;

    @Transactional
    public OrderResponse createOrder(OrderCreateRequest request, UUID userId) {
        // Validar en el service, no solo en el controller
        if (orderRepository.existsByUserIdAndStatus(userId, OrderStatus.PENDING)) {
            throw new ConflictException("User already has a pending order");
        }
        Order order = Order.create(request, userId);
        return OrderResponse.from(orderRepository.save(order));
    }
}
```

### PostgreSQL — CTEs para Legibilidad
```sql
WITH active_subscriptions AS (
    SELECT user_id, plan_id, expires_at
    FROM subscriptions
    WHERE expires_at > NOW() AND cancelled_at IS NULL
),
user_plans AS (
    SELECT u.id, u.email, p.name AS plan_name, s.expires_at
    FROM users u
    JOIN active_subscriptions s ON s.user_id = u.id
    JOIN plans p ON p.id = s.plan_id
)
SELECT * FROM user_plans ORDER BY expires_at;
```

---

## Herramientas del Proyecto

- `psql` — diagnóstico directo en PostgreSQL
- `/ck:docs-seeker` — documentación actualizada de frameworks
- `/ck:sequential-thinking` — problemas complejos de arquitectura
- `/ck:security` — auditorías de seguridad en endpoints
- `/ck:databases` — decisiones complejas de modelado y optimización
