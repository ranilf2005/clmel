# Start from Cisco pyATS base image (or python slim if you prefer)
FROM ciscotestautomation/pyats:latest

# Install OpenSSH client
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
      openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Add global SSH config to accept legacy crypto
RUN mkdir -p /etc/ssh && \
    echo "Host *" > /etc/ssh/ssh_config && \
    echo "    KexAlgorithms +diffie-hellman-group14-sha1" >> /etc/ssh/ssh_config && \
    echo "    HostKeyAlgorithms +ssh-rsa" >> /etc/ssh/ssh_config && \
    echo "    PubkeyAcceptedKeyTypes +ssh-rsa" >> /etc/ssh/ssh_config

# Set working directory
WORKDIR /workspace

# Default command
CMD ["/bin/bash"]

