FROM base:latest
EXPOSE 5000
CMD ["python", "library_service/app.py"]