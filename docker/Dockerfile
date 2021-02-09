FROM ubuntu:18.04

RUN apt -y update && apt install -y apt-utils && echo yes

RUN apt-get update

RUN DEBIAN_FRONTEND=noninteractive \
    apt install -y --no-install-recommends \
    make \
    gcc \
    git \
    file \
    pkg-config \
    wget \
    swig \
    netpbm \
    vim \
    less \
    zlib1g-dev \
    libbz2-dev \
    libcairo2-dev \
    libcfitsio-dev \
    libcfitsio-bin \
    libgsl-dev \
    curl \
    lsb-release \
    g++ \
    python3 \
    python3-dev \
    python3-pip \
    python3-pil \
    python3-tk \
    # # Remove APT files
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Python related stuff
RUN echo "../site-packages" > /usr/local/lib/python3.6/dist-packages/site-packages.pth

# pip installs
RUN for x in \
    setuptools \
    wheel \
    intel-numpy \
    intel-scipy \
    fitsio \
    matplotlib \
    zmq \
    ; do pip3 install "$x"; done \
    && rm -Rf /root/.cache/pip

# set prompt and default shell
SHELL ["/bin/bash", "-c"]
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["/bin/bash"]
RUN ln -s "$(which python3)" /usr/bin/python
ENV PATH /usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
WORKDIR /src/

RUN curl -L --remote-name https://bitbucket.org/mpaterno/cosmosis-bootstrap/raw/master/cosmosis-bootstrap-linux \
    && chmod u+x cosmosis-bootstrap-linux \
    && ./cosmosis-bootstrap-linux -p -r cosmosis \
    && cd cosmosis \
    && source config/setup-cosmosis \
    && make

ENV PYTHONPATH /src/cosmosis

RUN DEBIAN_FRONTEND=noninteractive \
    apt install -y --no-install-recommends \
    graphviz \
    graphviz-dev \
    # # Remove APT files
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# future for cosmosis
# pip installs
RUN for x in \
    numpy==1.19 \
    pyqt5==5.14 \
    cobaya[gui] \
    future \
    pygraphviz \
    pytest \
    sphinx \
    sphinx-rtd-theme \
    coveralls \
    ; do pip3 install "$x"; done \
    && rm -Rf /root/.cache/pip

COPY . /src/cosmopipe

ENV PYTHONPATH /src/cosmopipe:${PYTHONPATH}

WORKDIR /homedir/
