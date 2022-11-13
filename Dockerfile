FROM python:3.11.0-slim-bullseye

# Add a system user to process the service
RUN useradd -r -m -s /sbin/nologin dot
USER dot

# Change workdir and copy the service
WORKDIR /home/dot
COPY --chown=dot:dot dot_proxy.py .

# Indicate the service listen port
EXPOSE 53

# Run the service
CMD python dot_proxy.py
