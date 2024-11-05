FROM nvcr.io/nvidia/rapidsai/base:24.10-cuda12.0-py3.11
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN python -m pip install --upgrade pip
#RUN pip install     --extra-index-url=https://pypi.nvidia.com     cuml-cu12==24.10.*
RUN pip install --no-deps bertopic==0.16.2
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
RUN rm requirements.txt
RUN python3 -c "import nltk; nltk.download('stopwords')"
COPY ./ .
ENTRYPOINT ["python", "app.py"]

#RUN uvicorn api_reports:app --host 0.0.0.0 --port 8000 --reload
