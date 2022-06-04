FROM base
EXPOSE 5025
WORKDIR /backend
CMD ["python3", "ocr_service/server.py"]