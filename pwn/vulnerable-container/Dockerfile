FROM ubuntu:22.04

# Instalar sudo y herramientas básicas
RUN apt-get update && apt-get install -y \
    sudo \
    vim \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario vulnerable
RUN useradd -m -s /bin/bash ctfuser && \
    echo "ctfuser:ctfpassword" | chpasswd

# VULNERABILIDAD: sudo mal configurado
# Permite ejecutar vim como root sin password
RUN echo "ctfuser ALL=(ALL) NOPASSWD: /usr/bin/vim" >> /etc/sudoers

# Crear directorio compartido para monitoreo
RUN mkdir -p /monitored && chmod 755 /monitored

# Cambiar al usuario vulnerable
USER ctfuser
WORKDIR /home/ctfuser

# Mensaje de bienvenida
RUN echo 'echo "🎯 Objetivo: Crear el archivo /root/pwned.txt"' >> ~/.bashrc
RUN echo 'echo "💡 Pista: Revisa tus permisos sudo con: sudo -l"' >> ~/.bashrc

CMD ["/bin/bash"]