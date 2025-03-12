# GPU Reports
Este es un microservicio dedicado a ejecutar reportes que requieren la utilización de GPU.


# Arquitectura

Se trata de un micro servicio tipo API utilizando la libreria FastAPI. Cada endpoint resuelve un caso de uso.
La capa `services` contiene las conecciones a servicios de RD
La capa `core` contiene la lógica de negocio
La capa `api` expone los enpoints y coordina los servicios para la resolucion de los casos de uso.
Este microservicio es de acceso privado. (solo LAN)


# Endpoints

## Topics

Recibe informacion desde manager 


# Notas para la documentación

## Servicios de llm
Un script de servicio por cada backend? En principio deberíamos elegir uno y continuar con ese. Por ahora vLLM.

El método de generación general para un modelo instruct:
- Recibe una lista de listas cada una estructura de roles y mensaje, por ejemplo:
    ```python
    [
        {
            "role": "system",
            "content": prompt_template["system"],
        },
        {
            "role": "user",
            "content": prompt_template["user"].format(doc=content[idx])
        }
    ]
    ```
- Devuelve una diccionario con el siguiente formato (cada script de servicio deberá acomodar el formato):
    ```python
        {
            outputs: [
                {
                    text: "generated_text_1"
                    other_info: {}
                },
                {
                    text: "generated_text_1"
                    other_info: {}
                },
                etc...,
            ],
            general_info: {}
        }
    ```
    La idea es poder devolver información acerca de cada generación e información general.

## Modelos para descargar en Minio

- **llama3.2 3B instruct**: el que estamos usando actualmente.
- **deepseek R1 distill qwen 1.5B**: requiere revisar el format del output antes de implementarse.
- **qwen2.7 7B instruct 1M**: solo es posible utilizarlo en skynet.
Probar:
https://huggingface.co/tensorblock/Llama-3.2-8B-Instruct-GGUF/blob/main/Llama-3.2-8B-Instruct-Q3_K_M.gguf
https://huggingface.co/QuantFactory/Llama-3.2-3B-GGUF
https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF
https://huggingface.co/meta-llama/Llama-3.2-11B-Vision-Instruct/tree/main (en skynet - en proceso de descarga 27/02)

## Recursos útiles
- vllm classes
    - [RequestOutput](https://github.com/vllm-project/vllm/blob/main/vllm/outputs.py#L85)
    - [RequestMetrics](https://github.com/vllm-project/vllm/blob/main/vllm/sequence.py#L98)

    -----------
    -----------

# Documentación de Endpoints - Servicio `gpu_reports`

## Visión General

`gpu_reports` es un servicio que expone múltiples endpoints para ejecutar tareas de inferencia sobre documentos usando LLMs. Las funcionalidades incluyen clasificación, generación de resúmenes, ejecución de prompts y análisis temáticos.

---

## 1. POST /llm/classification

### Descripción

Clasifica documentos según un prompt específico. Devuelve cantidad total de documentos procesados y cuántos fueron clasificados.

### Parámetros del Payload

- `index_pattern`: Índice o patrón de índices.
- `since_date`, `to_date`: Rango de fechas.
- `filters`: Campos del documento a recuperar.
- `prompt`: Prompt dict (`system`, `user`).
- `update_field`: Campo donde se guarda la clasificación.
- `task_key`: Clave de la predicción en el JSON.
- `valid_labels`: Lista de etiquetas válidas.
- `max_ndocs`: Límite de documentos a procesar.

### Ejemplo

```python
payload = {
  "index_pattern": "in-marketing-honduras-2024",
  "since_date": "2024-10-05T03:00:00.000Z",
  "to_date": "2024-11-05T15:00:00.000Z",
  "filters": {"fields": ["_id", "created_at", "content", "source"]},
  "prompt": ipcva_prompt,
  "update_field": "food_post_type",
  "task_key": "type_of_posting",
  "valid_labels": ["RECIPES", "NUTRITIONAL INFORMATION", "RECOMMENDATIONS", "OTHERS"],
  "max_ndocs": 5
}
```

### Respuesta

```json
{"total_docs": 50, "updated_docs": 49}
```

---

## 2. POST /llm/prompt

### Descripción

Ejecuta un prompt libre y devuelve el texto generado.

### Parámetro

- `prompt`: Texto del usuario.

### Ejemplo

```python
payload = {"prompt": "Podrías decirme 5 nombres para mi gato?"}
```

### Respuesta

```json
{"response": "Aquí te dejo algunas sugerencias: ..."}
```

---

## 3. POST /llm/summary

### Descripción

Genera un resumen sobre documentos seleccionados. Variantes automáticas según parámetros:

- `prompt_summary`: si no se especifica `query` ni `summary_field`.
- `prompt_categories_summary`: si se pasa `summary_field`.
- `prompt_query_summary`: si se pasa `query`.

### Parámetros

- `index_pattern`, `since_date`, `to_date`, `filters`
- `prompt`: dict `system`, `user`
- `summary_field`: campo de agrupación por categoría (opcional)
- `query`: filtro adicional textual (opcional)
- `max_ndocs`: máximo documentos a analizar

### Ejemplo

```python
payload = {
  "index_pattern": "in-*",
  "since_date": "2024-11-04T05:00:00.000Z",
  "to_date": "2024-11-04T06:00:00.000Z",
  "filters": {"fields": ["_id", "content", "category"]},
  "prompt": summary_prompt,
  "summary_field": "sentiment_name",
  "query": "content: presidenta",
  "max_ndocs": 10
}
```

### Respuesta

La estructura de la respuesta dependerá del tipo de variante ejecutada:

- Si se utiliza `prompt_categories_summary` (especificando `summary_field`), el resultado será un diccionario donde cada clave corresponde a un valor distinto del campo `summary_field` (por ejemplo: `NEU`, `POS`, `NEG`, etc.).

```json
{
  "response": {
    "NEU": "Resumen correspondiente a NEU",
    "POS": "Resumen correspondiente a POS"
  }
}
```

- Si se utiliza `prompt_summary` o `prompt_query_summary` (sin `summary_field`), el resultado será un diccionario con una única clave `summary`.

```json
{
  "response": {
    "summary": "Resumen general del corpus o según query aplicada."
  }
}
```

### Comparación entre variantes de resumen

| Variante                    | Cuándo se activa                           | Propósito                                                |
|----------------------------|--------------------------------------------|----------------------------------------------------------|
| `prompt_summary`           | Sin `query` ni `summary_field`             | Resumen general del corpus                               |
| `prompt_categories_summary`| Cuando se incluye `summary_field`          | Un resumen por cada categoría distinta                   |
| `prompt_query_summary`     | Cuando se incluye `query` (sin `summary_field`) | Resumen de documentos filtrados por una query específica |



---

## 4. POST /topics

### Descripción

Genera análisis temático sobre los documentos recuperados. Devuelve estructura completa para visualización: pie chart, barplot, wordcloud, documentos representativos y títulos/summaries por tópico.

### Parámetros del Payload

- `index_pattern`: patrón de índice
- `since_date`, `to_date`: rango temporal
- `filters`: campos a recuperar
- `max_ndocs`: máximo de documentos

### Ejemplo

```python
payload = {
  "index_pattern": "in-rock_nacional-radios-2025",
  "since_date": "2024-01-01T05:00:00.000Z",
  "to_date": "2025-12-10T09:00:00.000Z",
  "filters": {"fields": ["_id", "content", "embedding", "category"]},
  "max_ndocs": 100
}
```

### Respuesta

```json
{
  "chart": {
    "PieChart": {"topics": [...]},
    "Barplot": {"topic_0": [...], "topic_1": [...]},
    "Wordcloud": {...},
    "DocumentGroup": {...},
    "TopicInfo": {"topic_0": {"title": "Recital 2025", "summary": "..."}}
  },
  "n_docs": 99
}
```

---




