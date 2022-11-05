FROM python:alpine3.16 AS base
EXPOSE 80
WORKDIR /app
COPY . /app
ENTRYPOINT ["python3"]
CMD ["manage.py", "runserver", "0.0.0.0:80"]
RUN pip3 install django requests django-ratelimit