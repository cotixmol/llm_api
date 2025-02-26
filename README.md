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

## Modelos