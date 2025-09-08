# Heavy CFD Docker Container with OpenFOAM
FROM ubuntu:20.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    curl \
    git \
    build-essential \
    cmake \
    python3 \
    python3-pip \
    python3-dev \
    libopenmpi-dev \
    openmpi-bin \
    libboost-all-dev \
    libcgal-dev \
    libmetis-dev \
    libscotch-dev \
    libptscotch-dev \
    libparmetis-dev \
    libhdf5-dev \
    libnetcdf-dev \
    libvtk7-dev \
    libgl1-mesa-glx \
    libglu1-mesa \
    freeglut3-dev \
    libxmu-dev \
    libxi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install OpenFOAM
RUN wget -O - https://dl.openfoam.org/gpg.key | apt-key add - \
    && add-apt-repository http://dl.openfoam.org/ubuntu \
    && apt-get update \
    && apt-get install -y openfoam8-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up OpenFOAM environment
RUN echo "source /opt/openfoam8/etc/bashrc" >> /root/.bashrc
ENV FOAM_INSTALL_DIR=/opt/openfoam8
ENV FOAM_RUN=/opt/openfoam8/run
ENV FOAM_APPBIN=/opt/openfoam8/platforms/linux64GccDPInt32Opt/bin
ENV FOAM_LIBBIN=/opt/openfoam8/platforms/linux64GccDPInt32Opt/lib
ENV PATH=$FOAM_APPBIN:$PATH
ENV LD_LIBRARY_PATH=$FOAM_LIBBIN:$LD_LIBRARY_PATH

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip3 install -r requirements.txt

# Copy application code
COPY . /app

# Create OpenFOAM case directories
RUN mkdir -p /app/openfoam_cases

# Expose port
EXPOSE 5000

# Set working directory
WORKDIR /app

# Start the application
CMD ["python3", "backend/f_backend.py"]
