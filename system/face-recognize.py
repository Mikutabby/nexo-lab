#!/usr/bin/env python3
"""
Reconocimiento facial para identificar a miku.
Usa OpenFace NN4 DNN para generar embeddings faciales (128-d).

Soporta múltiples perfiles para distintas condiciones (luz, posición, etc.)

Uso:
  face-recognize.py train [perfil]   -> Toma fotos y entrena un perfil
  face-recognize.py whoami           -> Identifica quién está frente a la cámara
  face-recognize.py list             -> Lista los perfiles guardados
"""

import cv2
import json
import os
import sys
import pickle
import numpy as np
import subprocess
import time
from pathlib import Path

# ─── Config ─────────────────────────────────────────────────────

CONFIG_FILE = Path.home() / ".nexo" / "config.json"

def load_config():
    """Carga la configuración desde ~/.nexo/config.json"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"user_name": "amigo"}

def get_user_name():
    """Obtiene el nombre del usuario desde la config"""
    config = load_config()
    return config.get("user_name", "amigo")

# ─── Rutas ────────────────────────────────────────────────────────

EMBEDDINGS_FILE = os.path.expanduser("~/.face_embeddings.pkl")
MODEL_FILE = os.path.expanduser("~/.local/share/opencv_models/nn4.small2.v1.t7")
DNN_PROTOTXT = os.path.expanduser("~/.local/share/opencv_models/deploy.prototxt")
DNN_CAFFEMODEL = os.path.expanduser("~/.local/share/opencv_models/res10_300x300_ssd_iter_140000.caffemodel")

INPUT_SIZE = 96
COSINE_THRESHOLD = 0.30

# ─── Redes (cargadas una sola vez) ───────────────────────────────

_face_detector = None
_face_embedder = None

def get_face_detector():
    global _face_detector
    if _face_detector is None:
        _face_detector = cv2.dnn.readNetFromCaffe(DNN_PROTOTXT, DNN_CAFFEMODEL)
    return _face_detector

def get_face_embedder():
    global _face_embedder
    if _face_embedder is None:
        _face_embedder = cv2.dnn.readNetFromTorch(MODEL_FILE)
    return _face_embedder


# ─── Cámara ──────────────────────────────────────────────────────

def reset_camera():
    try:
        subprocess.run(
            ["v4l2-ctl", "-d", "/dev/video0", "-c", "auto_exposure=3"],
            capture_output=True, timeout=3
        )
    except Exception:
        pass


def capture_face_rgb():
    """
    Toma foto, detecta la cara con DNN, 
    y devuelve la cara recortada en RGB (96x96) lista para OpenFace.
    Retorna (cara_rgb, None) o (None, error_msg).
    """
    reset_camera()
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    if not cap.isOpened():
        return None, "No se pudo abrir la cámara"

    codec = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    cap.set(cv2.CAP_PROP_FOURCC, codec)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    time.sleep(0.3)

    for _ in range(5):
        ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        return None, "No se pudo capturar la imagen"

    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detectar cara con DNN SSD
    net = get_face_detector()
    blob = cv2.dnn.blobFromImage(rgb, 1.0, (300, 300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()

    faces = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            x1, y1, x2, y2 = box.astype(int)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            if x2 > x1 and y2 > y1:
                faces.append((x1, y1, x2 - x1, y2 - y1))

    if len(faces) == 0:
        return None, "No se detectó ninguna cara"

    # Cara más grande
    (fx, fy, fw, fh) = max(faces, key=lambda f: f[2] * f[3])

    # Margen 10%
    mx, my = int(fw * 0.10), int(fh * 0.10)
    x1 = max(0, fx - mx)
    y1 = max(0, fy - my)
    x2 = min(w, fx + fw + mx)
    y2 = min(h, fy + fh + my)

    face_rgb = rgb[y1:y2, x1:x2]
    face_rgb = cv2.resize(face_rgb, (INPUT_SIZE, INPUT_SIZE))

    return face_rgb, None


# ─── Embeddings ──────────────────────────────────────────────────

def get_embedding(face_rgb):
    """Genera embedding de 128 dimensiones usando OpenFace NN4."""
    net = get_face_embedder()
    blob = cv2.dnn.blobFromImage(
        face_rgb, 1.0/255.0, (INPUT_SIZE, INPUT_SIZE),
        (0.5, 0.5, 0.5), swapRB=False
    )
    net.setInput(blob)
    embedding = net.forward()
    embedding = embedding / np.linalg.norm(embedding)
    return embedding.flatten()


def cosine_distance(a, b):
    """Distancia coseno: 0 = idéntico, 1 = opuesto."""
    return 1.0 - np.dot(a, b)


# ─── Carga/guarda de datos ──────────────────────────────────────

EMBEDDINGS_JSON = os.path.expanduser("~/.face_embeddings.json")

def load_profiles():
    """
    Carga los perfiles desde JSON (seguro) o pickle (legacy para migración).
    Retorna dict de perfiles.
    """
    # Intentar JSON primero (formato seguro)
    if os.path.exists(EMBEDDINGS_JSON):
        try:
            with open(EMBEDDINGS_JSON, "r") as f:
                data = json.load(f)
            # Convertir listas a numpy arrays
            for name, profile in data.get("profiles", {}).items():
                if "mean_embedding" in profile:
                    profile["mean_embedding"] = np.array(profile["mean_embedding"])
                if "all_embeddings" in profile:
                    profile["all_embeddings"] = [np.array(e) for e in profile["all_embeddings"]]
            return data.get("profiles", {})
        except Exception as e:
            print(f"⚠️ Error cargando JSON: {e}", file=sys.stderr)

    # Fallback: migrar de pickle legacy (VULNERABLE - solo para migración)
    if os.path.exists(EMBEDDINGS_FILE):
        try:
            import pickle
            print("⚠️ Migrando de pickle a JSON (formato seguro)...", file=sys.stderr)
            with open(EMBEDDINGS_FILE, "rb") as f:
                data = pickle.load(f)
            # Formato nuevo
            if "profiles" in data:
                profiles = data["profiles"]
            else:
                # Formato viejo
                profile = {
                    "mean_embedding": data["mean_embedding"],
                    "all_embeddings": data.get("all_embeddings", []),
                    "label": data.get("label", "miku"),
                    "created": time.time()
                }
                profiles = {"default": profile}
            # Guardar como JSON y eliminar pickle
            save_profiles(profiles)
            try:
                os.remove(EMBEDDINGS_FILE)
                print("✅ Migrado y pickle eliminado", file=sys.stderr)
            except OSError:
                pass
            return profiles
        except Exception as e:
            print(f"❌ Error migrando pickle: {e}", file=sys.stderr)

    return {}


def save_profiles(profiles):
    """Guarda los perfiles en archivo JSON (seguro)."""
    # Convertir numpy arrays a listas para JSON
    data_to_save = {"profiles": {}}
    for name, profile in profiles.items():
        saved_profile = dict(profile)
        if "mean_embedding" in saved_profile and hasattr(saved_profile["mean_embedding"], "tolist"):
            saved_profile["mean_embedding"] = saved_profile["mean_embedding"].tolist()
        if "all_embeddings" in saved_profile:
            saved_profile["all_embeddings"] = [
                e.tolist() if hasattr(e, "tolist") else e 
                for e in saved_profile["all_embeddings"]
            ]
        data_to_save["profiles"][name] = saved_profile
    
    with open(EMBEDDINGS_JSON, "w") as f:
        json.dump(data_to_save, f, indent=2)


# ─── Entrenamiento ───────────────────────────────────────────────

def train():
    """Toma fotos, calcula embeddings y guarda un nuevo perfil."""
    # Determinar nombre del perfil
    profile_name = "default"
    if len(sys.argv) >= 3:
        profile_name = sys.argv[2].strip().lower()
        if profile_name in ("train", "whoami", "list"):
            print(f"❌ '{profile_name}' no es un nombre de perfil válido")
            sys.exit(1)

    profile_key = f"miku_{profile_name}"

    embeddings = []
    n_photos = 15

    print(f"📸 Perfil: '{profile_key}' — {n_photos} fotos")
    print("   Mové un poco la cabeza entre cada una.")
    for i in range(n_photos):
        face, err = capture_face_rgb()
        if face is None:
            for intento in range(3):
                time.sleep(0.5)
                face, err = capture_face_rgb()
                if face is not None:
                    break
        if face is None:
            print(f"   ⏭️  Foto {i+1}/{n_photos}: {err}")
            continue

        emb = get_embedding(face)
        embeddings.append(emb)
        print(f"   🧬 {len(embeddings)}/{n_photos}")
        time.sleep(0.3)

    if len(embeddings) < 3:
        print("❌ No se pudieron capturar suficientes fotos (mínimo 3)")
        sys.exit(1)

    # Calcular embedding promedio (face signature)
    mean_emb = np.mean(embeddings, axis=0)
    mean_emb = mean_emb / np.linalg.norm(mean_emb)

    # Cargar perfiles existentes y agregar/actualizar
    profiles = load_profiles()
    user_name = get_user_name()
    profiles[profile_key] = {
        "mean_embedding": mean_emb,
        "all_embeddings": embeddings,
        "label": user_name,
        "created": time.time()
    }
    save_profiles(profiles)

    print(f"\n✅ Perfil '{profile_key}' guardado en {EMBEDDINGS_JSON}")

    # Auto-verificación
    dists = [cosine_distance(mean_emb, e) for e in embeddings]
    avg_dist = np.mean(dists)
    max_dist = np.max(dists)
    conf = (1 - avg_dist) * 100
    print(f"\n🔍 Distancia coseno promedio: {avg_dist:.4f} (ideal < {COSINE_THRESHOLD})")
    print(f"   Distancia máxima entre fotos: {max_dist:.4f}")
    print(f"   Confianza estimada: {conf:.0f}%")

    if avg_dist > COSINE_THRESHOLD:
        print("   ⚠️  Las fotos tienen mucha variación — tratá de mantener")
        print("       la cara más centrada y con buena luz")
    else:
        print("   ✅ Modelo consistente")
    print(f"🎉 Perfil '{profile_key}' entrenado!")


# ─── Listar perfiles ─────────────────────────────────────────────

def list_profiles():
    """Lista todos los perfiles guardados."""
    profiles = load_profiles()
    if not profiles:
        print("📭 No hay perfiles guardados.")
        print("   Ejecutá 'face-recognize.py train [nombre]' primero.")
        return

    print(f"📋 Perfiles guardados ({len(profiles)}):")
    print(f"   {'Perfil':<25} {'Fotos':<8} {'Creado':<20}")
    print(f"   {'-'*25} {'-'*8} {'-'*20}")
    for name, p in sorted(profiles.items()):
        n_fotos = len(p.get("all_embeddings", []))
        created = time.strftime("%Y-%m-%d %H:%M", time.localtime(p.get("created", 0)))
        print(f"   {name:<25} {n_fotos:<8} {created:<20}")


# ─── Reconocimiento ──────────────────────────────────────────────

def whoami():
    """
    Toma una foto y compara contra TODOS los perfiles guardados.
    Salidas:
      - "miku" + confianza si coincide con algún perfil miku (exit 0)
      - "unknown" + confianza si no coincide (exit 1)
      - "no_face" + error si no se detecta cara (exit 2)
    """
    profiles = load_profiles()
    if not profiles:
        print("no_face")
        print("❌ No hay perfiles entrenados.")
        print("   Ejecutá 'face-recognize.py train [nombre]' primero.")
        sys.exit(2)

    # Intentar capturar con reintentos
    face, err = capture_face_rgb()
    if face is None:
        for intento in range(3):
            time.sleep(0.5)
            face, err = capture_face_rgb()
            if face is not None:
                break
    if face is None:
        print("no_face")
        print(f"❌ {err}")
        sys.exit(2)

    test_emb = get_embedding(face)

    # Probar contra todos los perfiles, quedarse con el mejor
    best_dist = 999.0
    best_profile = None
    best_conf = 0.0

    for name, p in profiles.items():
        mean_emb = p["mean_embedding"]
        dist = cosine_distance(mean_emb, test_emb)
        conf = (1 - dist) * 100
        if dist < best_dist:
            best_dist = dist
            best_profile = name
            best_conf = conf

    # Decidir: si el mejor perfil es miku_*, es el usuario conocido
    # IMPORTANTE: la PRIMERA línea debe ser el estado (usuario/unknown/no_face)
    # para que check-identity.py pueda leerlo
    user_name = get_user_name()
    if best_dist < COSINE_THRESHOLD and best_profile and best_profile.startswith("miku_"):
        print("miku")
        print(f"👋 Hola {user_name}! (perfil: '{best_profile}', confianza: {best_conf:.0f}%)")
    else:
        print("unknown")
        if best_profile and best_profile.startswith("miku_"):
            print(f"🤔 Casi {user_name}! (distancia: {best_dist:.3f}, umbral: {COSINE_THRESHOLD:.2f})")
        else:
            print(f"🤔 No te reconozco. (mejor distancia: {best_dist:.3f})")

    # Debug: mostrar resultados de todos los perfiles (después del estado)
    print(f"📊 Mejor perfil: '{best_profile}' (distancia: {best_dist:.4f}, confianza: {best_conf:.0f}%)")
    for name, p in profiles.items():
        d = cosine_distance(p["mean_embedding"], test_emb)
        match = "✅" if d < COSINE_THRESHOLD else "❌"
        print(f"   {match} {name}: distancia {d:.4f}")

    if best_dist < COSINE_THRESHOLD and best_profile and best_profile.startswith("miku_"):
        sys.exit(0)
    else:
        sys.exit(1)


# ─── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: face-recognize.py [train|whoami|list] [nombre_perfil]")
        print("")
        print("  train [perfil]  -> Entrena un perfil (ej: 'iluminado', 'oscuro')")
        print("  whoami          -> Identifica quién está frente a la cámara")
        print("  list            -> Lista los perfiles guardados")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "train":
        train()
    elif cmd == "whoami":
        whoami()
    elif cmd == "list":
        list_profiles()
    else:
        print(f"Comando desconocido: {cmd}")
        print("Usá: train | whoami | list")
