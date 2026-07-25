# Manual Técnico para el Comprador — CareClearCrew Multi-Usuario y Multi-Tenant

Este manual detalla la arquitectura de autenticación, identidad, control de roles (RBAC), aislamiento multi-tenant e integridad criptográfica de **CareClearCrew**. Asimismo, explica los pasos para el despliegue en producción utilizando PostgreSQL en Render.

---

## 1. Arquitectura de Usuarios y Roles (RBAC)

El sistema ahora cuenta con un modelo robusto de usuarios y control de accesos basado en roles (RBAC) implementado en `src/care_clear_crew/auth.py` y persistido en `src/care_clear_crew/history_db.py`.

### Roles Definidos:
1. **`operativo`**:
   - Permiso para ejecutar análisis manuales y asíncronos completos.
   - Acceso al "Simulador Pre-Envío" para estimaciones de probabilidad de aprobación.
   - Visualización restringida en el **Historial**: únicamente puede ver y descargar los casos que él mismo generó.
2. **`administrador`**:
   - Hereda todos los permisos del rol operativo.
   - Capacidad para ver **todos los casos de su institución** en el Historial (no solo los propios).
   - Acceso exclusivo al **Panel Ejecutivo** (métricas acumuladas, ahorros de tiempo, gráficos por aseguradora y denegaciones recientes).
   - Acceso exclusivo a la sección **Gestión de Usuarios** para activar/desactivar cuentas y alternar roles de su misma institución.
   - Gestión y configuración del **Límite Mensual de Consumo** de análisis y configuración de alertas de consumo.

### Registro del Primer Administrador:
- Al registrar una institución nueva por primera vez, el sistema asigna automáticamente el rol de `administrador` al primer usuario registrado.
- Este administrador inicial tiene el control total para gestionar el acceso e invitar al resto del equipo médico operativo de su clínica.

---

## 2. Aislamiento Multi-Tenant (Multi-Clínicas)

El aislamiento multi-tenant es de nivel de base de datos y sesión activa. Ningún dato de una institución es visible o accesible desde otra, logrando un aislamiento del 100%.

- **Filtros por `institution_name`**: Todas las consultas a la base de datos de auditoría (`get_history`, `get_stats_summary`, `get_all_patterns`, etc.) están parametrizadas con la institución de la sesión activa del usuario actual.
- **Sin paso manual**: No es posible manipular el nombre de la clínica desde la interfaz de usuario; se deduce de manera segura del registro de sesión autenticada en `st.session_state`.
- **Límites e Integridad Aislados**: Los límites de consumo mensual, registros de auditoría y patrones aprendidos de aseguradoras se aíslan por completo por institución.

---

## 3. Integridad Criptográfica — Trust Ledger (Cadena de Bloques de Casos)

Para evitar la alteración maliciosa o manipulación del historial médico de decisiones, el sistema implementa un **Trust Ledger** criptográficamente encadenado en la tabla `authorization_requests`.

- **Generación de Hash**: Cada registro genera un hash criptográfico SHA-256 único (`record_hash`) que concatena:
  - El hash del caso anterior de la institución (`previous_hash`).
  - Datos clave del caso: `patient_name`, `policy_number`, `decision`.
  - El ID único del médico/creador (`created_by_user_id`).
- **Inmutabilidad**: Si alguien intenta alterar un caso anterior de manera manual directamente en la base de datos, el hash encadenado subsecuente se romperá, permitiendo que cualquier proceso de auditoría forense detecte inmediatamente la manipulación de la identidad o la decisión.

---

## 4. Soporte Dual de Base de Datos: SQLite & PostgreSQL

El sistema soporta de manera nativa y transparente dos motores de bases de datos gracias a la capa de abstracción en `history_db.py`.

### A. Fallback Local (SQLite)
Si la variable de entorno `DATABASE_URL` no está definida, el sistema inicializa una base SQLite local (`care_clear_history.db`). Esto es ideal para pruebas locales o desarrollo rápido de manera autónoma.

### B. Producción (PostgreSQL)
Para despliegues reales con múltiples usuarios recurrentes y escrituras concurrentes, se recomienda usar PostgreSQL. La conexión se realiza de forma automática al configurar la variable de entorno `DATABASE_URL`.

---

## 5. Guía de Despliegue en Render con PostgreSQL

El repositorio incluye una plantilla `render.yaml` pre-configurada para provisionar la base de datos Postgres y el servicio Streamlit en Render de forma integrada.

### Pasos para el Despliegue:
1. Conecta tu repositorio de GitHub a tu cuenta de Render.
2. Crea un nuevo **Blueprints** en Render seleccionando tu repositorio.
3. Render detectará el archivo `render.yaml` y creará automáticamente:
   - Una base de datos **PostgreSQL** (Render PostgreSQL).
   - Un servicio web **Streamlit** configurado en el puerto dinámico `$PORT`.
   - La variable de entorno `DATABASE_URL` conectando el backend con la base de datos de manera automatizada.
4. Completa las variables de entorno requeridas en el panel del servicio web de Render:
   - `OPENROUTER_API_KEY`: Tu API key para la inferencia con CrewAI.
   - `OPENROUTER_MODEL`: Modelo de lenguaje preferido (ej. `meta-llama/llama-3.3-70b-instruct`).

---

## 6. Proceso de Migración de SQLite a PostgreSQL

Si has recolectado datos previos en desarrollo con SQLite (`care_clear_history.db`) y deseas migrarlos a tu nueva base PostgreSQL de producción, utiliza el script proporcionado:

```bash
# Configura la URL de conexión de producción temporalmente
export DATABASE_URL="postgresql://usuario:password@host:puerto/nombre_db"

# Ejecuta el script de migración asistido
python src/care_clear_crew/migrate_to_postgres.py
```

El script copiará de forma segura todos tus usuarios existentes, solicitudes de autorización, firmas del Trust Ledger criptográfico, límites de consumo y registros de actividad sin alterar la integridad histórica.
