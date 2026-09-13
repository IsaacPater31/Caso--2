# CASO 2 (Factores de Certeza): Sistema Experto para el Triage de Incidentes de Ciberseguridad (IDS)

**Referencia:** Documento "Casos de estudio corte 1.pdf"

---

## 1. Lineamientos y Criterios de Evaluación

Para garantizar la transparencia y el rigor académico en este corte evaluativo (10% total de la asignatura), la entrega se rige bajo la siguiente distribución de puntajes y pautas:

### Criterios Detallados de Revisión:
* **Memorias de Cálculo Escritas (Teórico) [50%]:** Desarrollo matemático paso a paso y cálculo completo de propagación de factores de certeza.
* **Implementación Computacional [35%]:** Código fuente funcional, estructurado, modular y parametrizable (en Python o MATLAB) para el caso. El código debe poder evaluar cualquier valor nítido ingresado en tiempo de ejecución de manera interactiva.
* **Calidad del Reporte y Presentación [15%]:** Redacción técnica profesional, orden, claridad metodológica y cumplimiento riguroso de las pautas de presentación.

### Pautas de Entrega Adicionales:
* El taller debe ser desarrollado en parejas (grupos de máximo 2 personas).
* Las memorias de cálculo teóricas deben entregarse en un documento digital ordenado o PDF.
* El software debe subirse a la plataforma académica Classroom en un archivo comprimido (.zip) con los scripts correspondientes y un instructivo simple de ejecución (README).
* Se penalizará el plagio de código o la copia de soluciones con nota de 0.0 sin derecho a recuperación.

---

## 2. El Problema

En el Centro de Operaciones de Seguridad (SOC) de la Universidad de Cartagena, un sistema automatizado analiza constantemente múltiples alertas de sensores tecnológicos en busca de intrusiones en la red. Dada la naturaleza de los ataques informáticos, muchas de estas alertas son imprecisas o representan comportamientos que pueden o no ser maliciosos. Para clasificar estas amenazas de forma lógica bajo incertidumbre, se empleará la **Teoría de Factores de Certeza**.

### Hipótesis Diagnósticas y Evidencias del Sistema
El sistema experto evalúa de manera simultánea tres hipótesis exclusivas de incidentes (CH):
* **CH1:** Ataque de Denegación de Servicio Distribuido (DDoS)
* **CH2:** Intrusión de Ransomware / Secuestro de Archivos
* **CH3:** Falsa Alarma (Falso positivo por tráfico legítimo)

Los sensores de la red y del sistema operativo han arrojado las siguientes evidencias (E) con sus respectivos Factores de Certeza (CE) medidos en tiempo real:

| Código | Descripción de la Alerta del Sensor | Factor de Certeza (CE) |
| :--- | :--- | :--- |
| **E1** | Pico anómalo extremo en el consumo de ancho de banda entrante. | 0.85 |
| **E2** | Intentos masivos fallidos de autenticación SSH en puertos de servidores. | 0.90 |
| **E3** | Alertas del antivirus corporativo local en las terminales (endpoints). | -0.40 |
| **E4** | Modificaciones inexplicables en las firmas SHA-256 de archivos del sistema web. | 0.70 |

> **Nota teórica crítica:** Observe que el antivirus corporativo reporta CE(E3) = -0.40. En la teoría de factores de certeza, un factor negativo indica certidumbre de que el hecho NO ocurre (en este caso, indica que hay certeza moderada de que el antivirus NO ha detectado amenazas).

---

## 3. Base de Reglas del Sistema Experto de Seguridad

El motor de inferencia cuenta con las siguientes reglas lógicas con sus respectivos Factores de Certeza de Regla (CR/CF):

| ID Regla | Estructura Lógica (SI-ENTONCES) | Factor de Regla (CR) |
| :--- | :--- | :--- |
| **R1** | SI Pico de Ancho de Banda (E1) ENTONCES DDoS (CH1) | 0.80 |
| **R2** | SI Intentos fallidos SSH (E2) AND Cambios en Firmas (E4) ENTONCES Ransomware (CH2) | 0.75 |
| **R3** | SI Antivirus detecta amenazas (E3) ENTONCES Ransomware (CH2) | 0.60 |
| **R4** | SI NOT Pico de Ancho de Banda (NOT E1) OR Antivirus Inactivo (NOT E3) ENTONCES Falsa Alarma (CH3) | 0.50 |

---

## 4. Preguntas Teóricas y Ejercicios Analíticos (Entregables)

Los estudiantes deben desarrollar manualmente y justificar paso a paso las siguientes tareas correspondientes al Caso 2:

1. **EVALUACIÓN DE REGLAS Y PROPAGACIÓN DE CERTEZA:** Realice el cálculo analítico paso a paso para la propagación de certeza de cada una de las 4 reglas lógicas (R1 a R4). Justifique matemáticamente bajo qué condiciones teóricas del modelo de certeza se descartan o activan las reglas en función de las certezas negativas de sus antecedentes (por ejemplo, el caso de E3 en R3 y R4).
2. **CO-SUSCRIPCIÓN DE HIPÓTESIS:** Aplique las fórmulas de combinación de reglas para hipótesis concurrentes en caso de que múltiples reglas apoyen el mismo diagnóstico. Calcule los Factores de Certeza Finales para las hipótesis DDoS (CH1), Ransomware (CH2) y Falsa Alarma (CH3). Ordene las hipótesis de mayor a menor confianza y concluya cuál es la recomendación formal de triage que el sistema experto debe dar al operador de seguridad del SOC.
3. **ANÁLISIS DE SENSIBILIDAD DE INCERTIDUMBRE:** Explique de manera analítica cómo afectaría el diagnóstico si el factor de certeza de las alertas del antivirus (E3) cambiara de -0.40 a 0.60. Calcule de nuevo las hipótesis CH2 y CH3 bajo esta nueva condición clínica/técnica y discuta el comportamiento del sistema.
4. **PROGRAMACIÓN DE FACTORES DE CERTEZA:** Escriba un script parametrizable en Python que represente el motor de inferencia de modelo de Factor de certeza para este caso. El script debe recibir un vector con las certezas de las evidencias del sensor, aplicar la lógica de reglas compuestas con AND/OR/NOT, propagar los factores de certeza, resolver la concurrencia de reglas usando las ecuaciones acumulativas y devolver el diagnóstico final formateado de forma elegante en consola.
