FROM base
EXPOSE 5015
CMD ["python", "text_detector/server.py"]