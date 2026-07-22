# EXPLICACIÓN DEL PROYECTO: MedAuthAgent

MedAuthAgent es una solución de software empresarial de vanguardia diseñada para automatizar de extremo a extremo las autorizaciones previas médicas mediante agentes de inteligencia artificial y tecnología RAG (Retrieval-Augmented Generation). El sistema cruza expedientes médicos de pacientes contra políticas y reglas de seguros médicos utilizando el framework CrewAI, identificando discrepancias de forma precisa y emitiendo decisiones de aprobación o denegación en segundos.

---

## 1. Arquitectura del Sistema

El producto está diseñado sobre tres pilares fundamentales que aseguran la máxima velocidad y precisión quirúrgica en el procesamiento de información médica:

1. **Agente Autónomo Inteligente (MedAuthAgent Officer)**: Un rol experto de prior-authorization pre-configurado para revisar expedientes complejos, analizar coberturas, evaluar exclusiones y calcular puntuaciones de confianza basadas en hallazgos objetivos.
2. **Motor RAG Multiformato de CrewAI**: Se integra con los sistemas nativos `PDFKnowledgeSource`, `TXTKnowledgeSource`, y una implementación personalizada para `DOCXKnowledgeSource`. Toda la información se procesa y fragmenta de forma semántica.
3. **Búsqueda Semántica Rápida con ChromaDB y PDFSearchTool**: La indexación de los documentos se maneja mediante vectores integrados en ChromaDB, el motor de base de datos vectorial de alto rendimiento, optimizado para evitar latencia de red.
4. **Capa de Abstracción de LLMs**: Adaptada nativamente para OpenRouter, permitiendo el uso de modelos médicos avanzados como Llama 3.3 70B de forma económica y ultrarrápida.

---

## 2. Flujo de Trabajo (Pipeline de Decisión)

1. **Carga y Upload**: El usuario arrastra los documentos clínicos del paciente (historial médico, exámenes, laboratorios) y los manuales o reglas de la póliza de seguros en la sección superior de la UI.
2. **Indexación en ChromaDB**: Las fuentes de conocimiento se configuran y se inicia un proceso de embedding que fragmenta y vectoriza el contenido localmente.
3. **Análisis de 105+ Puntos de Control**: El agente realiza un escaneo clínico profundo de los documentos respondiendo a más de 100 puntos de control divididos en 7 categorías obligatorias de forma asíncrona.
4. **Emisión de Decisión y Confianza**: Se calcula el nivel de concordancia y se emite la resolución (Aprobado / Denegado) junto con un porcentaje de confianza del 0 al 100%.
5. **Generación del Paquete Consolidado (ZIP)**: El backend genera un informe elegante en PDF mediante la biblioteca ReportLab, el archivo explicativo Markdown, un JSON estructurado de los puntos evaluados, y los une junto con el documento original dentro de un ZIP listo para descargar.

---

## 3. Configuración de Variables de Entorno

Para operar de forma óptima y conectar el sistema con el proveedor OpenRouter, debe configurar las siguientes variables de entorno:

| Variable | Tipo | Descripción |
| :--- | :--- | :--- |
| `OPENROUTER_API_KEY` | Requerido | Clave API secreta de su cuenta en OpenRouter para transacciones LLM. |
| `OPENROUTER_MODEL` | Opcional | Identificador del modelo (Por defecto: `meta-llama/llama-3.3-70b-instruct`). |
| `OPENROUTER_BASE_URL`| Opcional | URL base de OpenRouter (Por defecto: `https://openrouter.ai/api/v1`). |
| `OPENAI_API_BASE` | Opcional | URL de redirección compatible para SDKs de OpenAI (`https://openrouter.ai/api/v1`). |
| `OPENAI_API_KEY` | Requerido | Clave API secundaria para resolver inicialización predeterminada de CrewAI. |

---

## 4. Los 105+ Puntos de Control Evaluados

El sistema evalúa rigurosamente 15 puntos específicos para cada una de las 7 categorías obligatorias, sumando un total de 105 criterios analizados por expediente:

### Categoría 1: Datos del paciente (15 Puntos)
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

### Categoría 2: Cobertura de la póliza (15 Puntos)
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

### Categoría 3: Documentación presentada (15 Puntos)
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

### Categoría 4: Requisitos de la aseguradora (15 Puntos)
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

### Categoría 5: Cumplimiento y regulaciones (15 Puntos)
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

### Categoría 6: Análisis de riesgos (15 Puntos)
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

### Categoría 7: Factores de decisión (15 Puntos)
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

## 5. Instrucciones de Despliegue en Render

Siga estos sencillos pasos para lanzar **MedAuthAgent** a producción usando el plan gratuito de Render:

1. **Crear una Cuenta**: Regístrese en [Render](https://render.com).
2. **Conectar Repositorio**: Vincule su cuenta de GitHub o GitLab con Render.
3. **Seleccionar Aplicación Web**: Cree un nuevo servicio web y elija el repositorio `med-auth-agent`.
4. **Cargar Configuración**: Render detectará automáticamente el archivo `render.yaml` y configurará el servicio con el runtime de Python, comandos de compilación e inicio.
5. **Configurar Variables de Entorno**: Ingrese su clave API secreta `OPENROUTER_API_KEY` en la sección de Variables de Entorno de Render.
6. **Lanzar Despliegue**: Haga clic en Deploy. Su servicio estará listo para su uso y comercialización en menos de 60 segundos.
