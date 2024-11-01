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

