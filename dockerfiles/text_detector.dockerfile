FROM base
EXPOSE 5015
CMD ["python3", "-m", "flask", "run"]