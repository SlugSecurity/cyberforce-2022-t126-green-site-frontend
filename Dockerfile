FROM python:alpine3.16 AS base
EXPOSE 8000
WORKDIR /app
COPY . /app
ENTRYPOINT ["python3"]
CMD ["manage.py", "runserver", "0.0.0.0:8000"]
RUN pip3 install django requests