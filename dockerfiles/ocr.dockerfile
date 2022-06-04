FROM base
EXPOSE 5025
CMD ["python", "ocr_service/server.py"]