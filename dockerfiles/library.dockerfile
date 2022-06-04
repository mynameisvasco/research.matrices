FROM base
EXPOSE 5035
WORKDIR /backend
CMD ["python3", "library_service/app.py"]