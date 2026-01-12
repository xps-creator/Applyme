FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY src /app/src
RUN pip install --no-cache-dir \
  fastapi==0.115.8 \
  uvicorn[standard]==0.34.0 \
  psycopg[binary]==3.2.4 \
  sqlalchemy==2.0.37 \
  pydantic==2.10.6 \
  python-jose==3.3.0 \
  passlib[bcrypt]==1.7.4 \
  requests==2.32.3
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]