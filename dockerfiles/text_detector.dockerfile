FROM base
EXPOSE 5015
WORKDIR /backend
CMD ["python3", "ocr_service/server.py"]