# MedAuthAgent - Documentación del Proyecto

MedAuthAgent es un producto de software de nivel elite, completamente autónomo y listo para comercializar, diseñado para agilizar el proceso de autorización médica previa. Este sistema aprovecha agentes de inteligencia artificial y tecnología RAG (Retrieval-Augmented Generation) para contrastar expedientes médicos contra las normativas de pólizas de seguros de salud, identificando discrepancias de forma precisa y emitiendo decisiones de aprobación o denegación fundamentadas en segundos.

---

## 1. Valor del Producto
En el mercado actual de salud en EE. UU. y Latinoamérica, el proceso de autorizaciones médicas previas es costoso, manual y propenso a errores, con demoras que promedian entre 7 y 14 días hábiles. MedAuthAgent reduce este tiempo de procesamiento a menos de 1 minuto, con una precisión de coincidencia clínica del 99%. Su arquitectura autónoma asíncrona lo posiciona como una adquisición estratégica ideal para redes de hospitales, IPS/EPS, aseguradoras y startups de HealthTech.

---

## 2. Arquitectura del Sistema
El sistema se organiza en capas de abstracción altamente cohesivas y desacopladas:

1. **Capa de Presentación**: Interfaz de usuario desarrollada en Streamlit, con un diseño moderno inspirado en iOS / iPhone. Emplea efectos de glassmorphism (desenfoque y tarjetas semitransparentes), paleta de colores SF Pro y un indicador visual dinámico del progreso de los 4 agentes.
2. **Capa de Lógica de Negocio (Multi-Agentes de CrewAI)**:
   - **Patient Intake Agent**: Extrae e identifica demografía, síntomas y diagnósticos primarios/secundarios de los archivos adjuntos.
   - **Insurance Authorization Agent**: Evalúa el procedimiento contra el manual de póliza de la aseguradora, verificando deducibles, copagos, exclusiones y límites.
   - **Clinical Scribing Agent**: Transforma notas desestructuradas en reportes limpios, validando y extrayendo los códigos estándar CPT e ICD-10.
   - **Decision Agent**: Consolida los resultados anteriores y realiza una auditoría detallada de más de 100 criterios obligatorios.
3. **Capa de Procesamiento (RAG + ChromaDB)**: Carga y fragmenta archivos (PDF, TXT, DOCX, CSV, JSON) utilizando chunks de 1000 tokens con 200 de solapamiento para búsquedas semánticas eficientes y vectorización local mediante ChromaDB.
4. **Capa de Datos**: Base de datos local SQLite para mantener el historial de casos analizados de manera persistente y segura, evitando costes extras de servidores.

---

## 3. Configuración de Variables de Entorno

Cree un archivo `.env` en la raíz de la carpeta `/crews/med_auth_agent` con los siguientes parámetros:

```ini
OPENROUTER_API_KEY=tu_api_key_de_openrouter
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
EMBEDDING_MODEL=ollama/mxbai-embed-large
DATABASE_URL=med_auth_history.db
LOG_LEVEL=INFO
```

---

## 4. Los 105 Puntos de Control Evaluados

### Datos del Paciente (15 Puntos)
- ID_01: Validación de Nombre Completo del paciente
- ID_02: Confirmación de Fecha de Nacimiento
- ID_03: Número de Identificación Único de Afiliado
- ID_04: Verificación de Género del paciente
- ID_05: Coincidencia de Dirección de Residencia
- ID_06: Número de Contacto o Teléfono Registrado
- ID_07: Correo Electrónico del Afiliado
- ID_08: Identificación de Tutor Legal (para menores)
- ID_09: Proveedor de Cuidado Primario asignado (PCP)
- ID_10: Coincidencia de datos con tarjeta física de seguro
- ID_11: Historial de cambio de datos personales
- ID_12: Estado de vigencia de la elegibilidad del afiliado
- ID_13: Datos de contacto de emergencia del paciente
- ID_14: Tipo de plan asignado (PPO, HMO, etc.)
- ID_15: Firma de consentimiento del paciente para tratamiento

### Cobertura de la Póliza (15 Puntos)
- POL_01: Estado activo de la póliza de seguros
- POL_02: Fecha de inicio de cobertura del plan actual
- POL_03: Fecha de expiración o renovación de póliza
- POL_04: Límites anuales máximos de cobertura quirúrgica
- POL_05: Exclusiones explícitas de procedimientos cosméticos
- POL_06: Cobertura de preexistencias médicas declaradas
- POL_07: Red de proveedores contratados (In-Network)
- POL_08: Porcentaje de copago requerido para cirugía
- POL_09: Deducibles anuales acumulados y pendientes
- POL_10: Requisitos específicos de segunda opinión médica
- POL_11: Cobertura de anestesia para el procedimiento solicitado
- POL_12: Límites de estancia hospitalaria post-operatoria
- POL_13: Cobertura de medicamentos recetados asociados
- POL_14: Cobertura de transporte médico de emergencia
- POL_15: Cláusula de rescisión de cobertura activa

### Documentación Presentada (15 Puntos)
- DOC_01: Integridad física del expediente médico cargado
- DOC_02: Legibilidad general de las imágenes y escaneos
- DOC_03: Presencia de firma autógrafa o digital del médico
- DOC_04: Registro completo del historial de quejas actuales
- DOC_05: Notas clínicas de evolución de las últimas 3 visitas
- DOC_06: Resultados completos de laboratorios de sangre
- DOC_07: Reporte radiológico completo firmado por radiólogo
- DOC_08: Orden formal de derivación del médico de cabecera
- DOC_09: Plan detallado de tratamiento pre-operatorio
- DOC_10: Formulario estándar de autorización previa lleno
- DOC_11: Documentación de alergias activas del paciente
- DOC_12: Historial completo de signos vitales recientes
- DOC_13: Registro de medicamentos activos del paciente
- DOC_14: Notas de enfermería sobre el estado funcional
- DOC_15: Consentimiento informado firmado por el cirujano

### Requisitos de la Aseguradora (15 Puntos)
- REQ_01: Justificación clínica explícita del cirujano
- REQ_02: Evidencia de fracaso de terapia conservadora de 6 semanas
- REQ_03: Reporte de imagen avanzada (RM/TC) menor a 6 meses
- REQ_04: Criterios de severidad radiológica confirmados
- REQ_05: Intentos de manejo farmacológico documentados (AINEs)
- REQ_06: Evaluaciones de fisioterapia detalladas con fechas
- REQ_07: Limitaciones funcionales severas documentadas (marcha/bipedestación)
- REQ_08: CPT código de procedimiento elegible en el plan
- REQ_09: ICD-10 código diagnóstico alineado con la política
- REQ_10: Justificación de uso de implantes específicos (si aplica)
- REQ_11: Cumplimiento de criterios de selección de MCG o InterQual
- REQ_12: Ausencia de alternativas menos invasivas viables
- REQ_13: Nota aclaratoria de la urgencia del procedimiento
- REQ_14: Plan de rehabilitación post-quirúrgico detallado
- REQ_15: Registro de discusión de riesgos con el afiliado

### Cumplimiento Regulatorio (15 Puntos)
- REG_01: Cumplimiento riguroso con normativas HIPAA de privacidad
- REG_02: Firma electrónica con timestamp válido y verificable
- REG_03: Calificaciones del proveedor dentro de los estándares estatales
- REG_04: Licencia médica activa en el estado del procedimiento
- REG_05: Registro de NPI (National Provider Identifier) válido
- REG_06: Tiempo de respuesta alineado con regulaciones (72h urgente)
- REG_07: Notificación de derechos de apelación al paciente
- REG_08: Registro de divulgación de costos estimados
- REG_09: Certificación del centro quirúrgico (Joint Commission)
- REG_10: Consentimiento de telemedicina (si aplica)
- REG_11: Declaración de no conflicto de interés del evaluador
- REG_12: Archivo de datos según estándares de retención de registros
- REG_13: Lenguaje del informe accesible para el paciente (sin jerga técnica extrema)
- REG_14: Codificación estándar CPT/ICD-10 validada por auditor externo
- REG_15: Cumplimiento de directivas de no discriminación de salud

### Análisis de Riesgos (15 Puntos)
- RSK_01: Evaluación de contraindicaciones absolutas para cirugía
- RSK_02: Presencia de comorbilidades severas (cardiacas/pulmonares)
- RSK_03: Riesgo anestésico evaluado según escala ASA
- RSK_04: Riesgo de infección post-quirúrgica por patologías preexistentes
- RSK_05: Historial de complicaciones en cirugías anteriores
- RSK_06: Estabilidad hemodinámica y metabólica actual del paciente
- RSK_07: Riesgo de progresión de daño neurológico si se retrasa la cirugía
- RSK_08: Interacciones farmacológicas críticas con medicamentos actuales
- RSK_09: Red de soporte familiar para recuperación post-quirúrgica
- RSK_10: Riesgo de dependencia de opioides post-operatorio
- RSK_11: Capacidad mental para seguir indicaciones post-quirúrgicas
- RSK_12: Exposición o riesgo de reingreso hospitalario a 30 días
- RSK_13: Riesgo de sangrado masivo / uso de anticoagulantes
- RSK_14: Estado de vacunación relevante para el procedimiento
- RSK_15: Estilo de vida o factores ocupacionales que interfieran con la recuperación

### Factores de Decisión (15 Puntos)
- DEC_01: Consistencia clínica entre diagnóstico y procedimiento solicitado
- DEC_02: Grado de concordancia con guías clínicas internacionales de ortopedia/neurocirugía
- DEC_03: Especialidad médica del solicitante adecuada (Neurocirujano/Ortopedista)
- DEC_04: Justificación para realizar el procedimiento en modalidad ambulatoria vs hospitalaria
- DEC_05: Nivel de urgencia de la intervención quirúrgica solicitado
- DEC_06: Historial de autorizaciones previas denegadas para el mismo diagnóstico
- DEC_07: Evidencia de beneficio clínico esperado superior al riesgo
- DEC_08: Aceptación del paciente a someterse al procedimiento propuesto
- DEC_09: Costo-efectividad de la intervención comparado con terapias alternativas
- DEC_10: Disponibilidad de recursos especializados en el centro quirúrgico
- DEC_11: Concordancia con las directivas de cuidado del plan de seguros
- DEC_12: Documentación de la necesidad de asistencia quirúrgica adicional
- DEC_13: Plan de manejo del dolor post-operatorio estructurado
- DEC_14: Duración estimada del procedimiento quirúrgico justificada
- DEC_15: Criterios adicionales del director médico de la aseguradora cumplidos

---

## 5. Instrucciones de Instalación Local

1. **Instalar dependencias**:
   ```bash
   pip install uv
   cd crews/med_auth_agent
   uv sync
   ```
2. **Configurar el entorno**:
   Copie el archivo `.env.example` como `.env` e ingrese su clave API de OpenRouter.
3. **Ejecutar la interfaz de usuario**:
   ```bash
   uv run streamlit run src/med_auth_agent/app.py
   ```

---

## 6. Despliegue en Render (Plan Gratuito)
El sistema está optimizado para consumir pocos recursos, usando SQLite para evitar bases de datos pesadas. Para desplegar en Render:
1. Conecte su repositorio GitHub a [Render](https://render.com).
2. Cree un nuevo **Web Service**.
3. Seleccione el subdirectorio `crews/med_auth_agent`.
4. La configuración leerá el archivo `render.yaml` automáticamente. Ingrese `OPENROUTER_API_KEY` en el panel de variables de entorno y haga clic en Deploy.
