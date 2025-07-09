FROM python:3.12
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY app.py ./
EXPOSE 8000
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "app:app", "--root-path", "/api/filestorage"]