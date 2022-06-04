FROM base
EXPOSE 5015
CMD ["python3", "text_detector/server.py"]