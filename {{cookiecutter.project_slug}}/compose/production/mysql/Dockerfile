FROM docker.io/mysql:8.4

COPY ./compose/production/mysql/maintenance /usr/local/bin/maintenance
RUN chmod +x /usr/local/bin/maintenance/* \
    && mv /usr/local/bin/maintenance/* /usr/local/bin \
    && rmdir /usr/local/bin/maintenance
