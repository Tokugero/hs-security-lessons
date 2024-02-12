FROM lscr.io/linuxserver/rdesktop:ubuntu-kde

RUN apt-get update && apt-get install -y \
    wget && \
    wget -q https://repos.influxdata.com/influxdata-archive_compat.key && \
    echo '393e8779c89ac8d958f81f942f9ad7fb82a25e133faddaf92e15b16e6ac9ce4c influxdata-archive_compat.key' | sha256sum -c && cat influxdata-archive_compat.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null && \
    echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | tee /etc/apt/sources.list.d/influxdata.list && \
    apt-get update && apt-get install -y telegraf

COPY files/telegraf.sh /custom-cont-init.d/telegraf.sh

RUN apt-get update && \
    apt-get install -y \
    gedit \
    gameconqueror \
    manaplus \
    openssh-server

COPY "files/ForensicsQuestion1" "/config/Desktop/ForensicsQuestion1"

RUN useradd paarthurnax

COPY "files/ForensicsQuestion2" "/config/Desktop/ForensicsQuestion2"

RUN mkdir -p /home/esbern/Downloads && touch /home/esbern/Downloads/foo.mp3

COPY files/README /config/Desktop/README

RUN useradd ballen && \
    useradd sheogorath && \
    useradd ulfric && \
    useradd esbern -p papAq5PwY/QQM

# Bump