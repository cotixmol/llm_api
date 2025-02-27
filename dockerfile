#RUN uvicorn api_reports:app --host 0.0.0.0 --port 8000 --reload
#################### BASE BUILD IMAGE ####################
# La parte más pesada de la imagen es la instalación de vllm 
FROM python:3.11.4-slim-bullseye AS base


RUN python -m pip install --upgrade pip
RUN pip install vllm==0.7.2
RUN pip install --no-deps bertopic==0.16.2

WORKDIR /app

#################### BASE BUILD IMAGE ####################

#################### GPU REPORTS IMAGE ####################
# Imagen que se usa en el repo de gpu_reports
FROM base AS gpu_reports

COPY ./requirements.txt ./requirements.txt 
RUN pip install -r requirements.txt
RUN rm requirements.txt

COPY ./ .

ENTRYPOINT ["python", "app.py"]

#################### GPU REPORTS IMAGE ####################