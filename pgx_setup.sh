#!/usr/bin/env bash
# PGX one-shot bootstrap: Isaac Sim 5.1 + Isaac Lab v2.3.2 + RoboMimic + GR1T2 seed dataset
# Target: NVIDIA GB10 (aarch64 + Blackwell) on Ubuntu 24.04
# Runs unattended. Log: ~/pgx_setup.log

set -e
exec > >(tee -a "$HOME/pgx_setup.log") 2>&1
echo "===== START $(date) ====="

cd "$HOME"

# ---- 1. OS packages (needs sudo cached) ----
echo "[1/7] apt packages..."
sudo apt-get update -y
sudo apt-get install -y git curl wget build-essential cmake \
    libglu1-mesa libxi-dev libxrandr-dev libxcursor-dev libxinerama-dev \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    pciutils unzip jq htop tmux

# ---- 2. Miniforge (conda for aarch64) ----
if [ ! -d "$HOME/miniforge3" ]; then
    echo "[2/7] Installing miniforge..."
    wget -q https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh -O /tmp/mf.sh
    bash /tmp/mf.sh -b -p "$HOME/miniforge3"
fi
export PATH="$HOME/miniforge3/bin:$PATH"
source "$HOME/miniforge3/etc/profile.d/conda.sh"

# ---- 3. Conda env ----
echo "[3/7] Creating conda env isaaclab (python 3.11)..."
if ! conda env list | grep -q "^isaaclab "; then
    conda create -n isaaclab python=3.11 -y
fi
conda activate isaaclab
pip install --upgrade pip

# ---- 4. Isaac Sim 5.1 (pip, ARM64 wheel) ----
echo "[4/7] Installing Isaac Sim 5.1.0.0..."
pip install isaacsim[all]==5.1.0.0 --extra-index-url https://pypi.nvidia.com

# ---- 5. Isaac Lab v2.3.2 ----
echo "[5/7] Cloning + installing Isaac Lab v2.3.2..."
if [ ! -d "$HOME/IsaacLab" ]; then
    git clone https://github.com/isaac-sim/IsaacLab.git --branch v2.3.2 "$HOME/IsaacLab"
fi
cd "$HOME/IsaacLab"
# IsaacLab installer handles all deps including pinocchio + pin-pink (ARM = official supported)
./isaaclab.sh --install

# ---- 6. RoboMimic ----
echo "[6/7] Installing RoboMimic..."
pip install robomimic

# ---- 7. GR1T2 seed dataset ----
echo "[7/7] Downloading GR1T2 seed dataset..."
mkdir -p "$HOME/IsaacLab/datasets"
# Try NGC public asset URL (Isaac Lab mimic GR1T2 annotated dataset)
DATASET_URL="https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/IsaacLab-Mimic/dataset_annotated_gr1.hdf5"
if [ ! -f "$HOME/IsaacLab/datasets/dataset_annotated_gr1.hdf5" ]; then
    wget -q "$DATASET_URL" -O "$HOME/IsaacLab/datasets/dataset_annotated_gr1.hdf5" || \
        echo "WARN: seed dataset download failed, will need manual upload"
fi

echo "===== DONE $(date) ====="
echo ""
echo "Verify with:"
echo "  source ~/miniforge3/etc/profile.d/conda.sh && conda activate isaaclab"
echo "  cd ~/IsaacLab && ./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py --headless"
