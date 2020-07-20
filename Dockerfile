FROM python:3
RUN pip install --upgrade --no-cache-dir fzfaws
WORKDIR /root
ENTRYPOINT ["fzfaws"]
