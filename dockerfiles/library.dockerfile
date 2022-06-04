FROM base
EXPOSE 5035
CMD ["python3", "-m", "flask", "run"]