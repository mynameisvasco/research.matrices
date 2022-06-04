FROM base
EXPOSE 5025
CMD ["python3", "-m", "flask", "run"]