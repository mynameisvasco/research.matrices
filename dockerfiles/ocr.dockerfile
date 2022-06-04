FROM base
EXPOSE 5025
CMD ["python3", "ocr_service/server.py"]