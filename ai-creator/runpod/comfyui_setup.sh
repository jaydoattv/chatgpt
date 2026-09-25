#!/usr/bin/env bash
# ComfyUI für Milena auf dem Network Volume einrichten. Einmalig; erneutes Ausführen ist gefahrlos
# (vorhandene, vollständige Dateien werden übersprungen, abgebrochene Downloads fortgesetzt).
#
#   bash comfyui_setup.sh              ComfyUI + Nodes + Bildmodelle Z-Image (~21 GB)
#   bash comfyui_setup.sh --video      zusätzlich Wan 2.2 Image-to-Video (~38 GB)
#   bash comfyui_setup.sh --nur-code   nur ComfyUI + Nodes + Gesichtserkennung, keine großen Modelle
#
# Getestete Stände (25.09.2026): ComfyUI 88ab4a0, Impact Pack 429d015, Impact Subpack 50c7b71.
# Alle Modelle sind öffentlich – kein Hugging-Face-Token nötig.
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"
COMFY="$WORKSPACE/ComfyUI"
VENV="${VENV:-$WORKSPACE/venv_comfy}"

VIDEO=0
MODELLE=1
for arg in "$@"; do
  case "$arg" in
    --video) VIDEO=1 ;;
    --nur-code) MODELLE=0 ;;
    *) echo "Unbekannte Option: $arg" >&2; exit 2 ;;
  esac
done

COMFY_COMMIT=88ab4a06566454ad89db8f0bedb970d6c08cd1b7
IMPACT_COMMIT=429d0159ad429e64d2b3916e6e7be9c22d025c3c
SUBPACK_COMMIT=50c7b71a6a224734cc9b21963c6d1926816a97f1

hole_repo() {  # url ziel commit
  local url=$1 ziel=$2 commit=$3
  if [ ! -d "$ziel/.git" ]; then
    git clone --quiet --filter=blob:none "$url" "$ziel"
  fi
  if ! git -C "$ziel" cat-file -e "${commit}^{commit}" 2>/dev/null; then
    git -C "$ziel" fetch --quiet origin
  fi
  git -C "$ziel" checkout --quiet "$commit"
  echo "ok  $(basename "$ziel") @ ${commit:0:7}"
}

lade() {  # url zielordner erwartete_bytes
  local url=$1 ordner=$2 bytes=$3
  local datei
  datei="$ordner/$(basename "$url")"
  mkdir -p "$ordner"
  if [ -f "$datei" ]; then
    local vorhanden
    vorhanden=$(stat -c %s "$datei")
    if [ "$vorhanden" = "$bytes" ]; then
      echo "ok  $(basename "$datei") (schon vorhanden)"
      return
    fi
    if [ "$vorhanden" -gt "$bytes" ]; then
      rm -f "$datei"
    fi
  fi
  echo "... lade $(basename "$datei") ($((bytes / 1024 / 1024)) MB)"
  curl -L --fail --retry 5 --retry-delay 5 -C - -o "$datei" "$url"
  local ist
  ist=$(stat -c %s "$datei")
  if [ "$ist" != "$bytes" ]; then
    echo "FEHLER: $(basename "$datei") hat $ist statt $bytes Bytes. Skript erneut starten (setzt fort)." >&2
    exit 1
  fi
  echo "ok  $(basename "$datei")"
}

echo "== 1/4 ComfyUI und Nodes"
hole_repo https://github.com/comfyanonymous/ComfyUI.git "$COMFY" "$COMFY_COMMIT"
hole_repo https://github.com/ltdrdata/ComfyUI-Impact-Pack.git "$COMFY/custom_nodes/ComfyUI-Impact-Pack" "$IMPACT_COMMIT"
hole_repo https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git "$COMFY/custom_nodes/ComfyUI-Impact-Subpack" "$SUBPACK_COMMIT"

echo "== 2/4 Python-Umgebung ($VENV)"
if [ ! -x "$VENV/bin/python" ]; then
  # --system-site-packages: nutzt das vorinstallierte CUDA-PyTorch des Pod-Images
  python3 -m venv --system-site-packages "$VENV"
fi
"$VENV/bin/python" -m pip install --quiet --upgrade pip
"$VENV/bin/python" -m pip install --quiet \
  -r "$COMFY/requirements.txt" \
  -r "$COMFY/custom_nodes/ComfyUI-Impact-Pack/requirements.txt" \
  -r "$COMFY/custom_nodes/ComfyUI-Impact-Subpack/requirements.txt"
"$VENV/bin/python" -c "import torch; print('ok  torch', torch.__version__, '| CUDA verfügbar:', torch.cuda.is_available())"

echo "== 3/4 Gesichtserkennung für den FaceDetailer"
lade https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8m.pt "$COMFY/models/ultralytics/bbox" 52026019
mkdir -p "$COMFY/models/loras"

if [ "$MODELLE" = 1 ]; then
  echo "== 4/4 Bildmodelle Z-Image (Base)"
  lade https://huggingface.co/Comfy-Org/z_image/resolve/main/split_files/diffusion_models/z_image_bf16.safetensors "$COMFY/models/diffusion_models" 12309866400
  lade https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors "$COMFY/models/text_encoders" 8044982048
  lade https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors "$COMFY/models/vae" 335304388
  if [ "$VIDEO" = 1 ]; then
    echo "== Video: Wan 2.2 14B Image-to-Video"
    lade https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors "$COMFY/models/diffusion_models" 14294742832
    lade https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors "$COMFY/models/diffusion_models" 14294742832
    lade https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors "$COMFY/models/text_encoders" 6735906897
    lade https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors "$COMFY/models/vae" 253815318
    lade https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors "$COMFY/models/loras" 1226977424
    lade https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors "$COMFY/models/loras" 1226977424
  fi
else
  echo "== 4/4 übersprungen (--nur-code)"
fi

echo
echo "Fertig. Start: bash $(dirname "$0")/comfyui_start.sh"
df -h "$WORKSPACE" | tail -1 | awk '{print "Speicher auf dem Volume: " $3 " belegt, " $4 " frei"}'
