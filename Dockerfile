FROM python:3.12
EXPOSE 8080
WORKDIR /app
COPY . ./
RUN pip install -r requirements.txt
ENTRYPOINT ["streamlit", "run", "Healthcare-System.py", "--server.port=8080", "--server.address=0.0.0.0"]
