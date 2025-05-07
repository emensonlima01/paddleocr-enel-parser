# ======================
# IMPORTAÇÕES E CONFIGS
# ======================
import os
import json
from dotenv import load_dotenv
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

# Carregar variáveis do arquivo .env
load_dotenv()
pdf_path = os.getenv('PDF_PATH')
# O nome do JSON de saída será igual ao do PDF, trocando a extensão por .json
output_json_path = os.path.splitext(pdf_path)[0] + '.json'

# Caminho relativo ao diretório do script para o poppler
base_dir = os.path.dirname(os.path.abspath(__file__))
poppler_path = os.path.join(
    base_dir,
    "layer", "poppler", "layer", "poppler", "poppler-23.11.0", "Library", "bin"
)

# ======================
# CONVERSÃO PDF -> IMAGEM
# ======================
images = convert_from_path(
    pdf_path,
    poppler_path=poppler_path,
    first_page=1,
    last_page=1,
    dpi=400
)

# ======================
# PRÉ-PROCESSAMENTO DA IMAGEM
# ======================
def preprocess_image(img):
    # Converter para escala de cinza
    img = img.convert('L')
    # Aumentar contraste
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    # Binarização (threshold)
    img = img.point(lambda x: 0 if x < 180 else 255, '1')
    # Remover ruído (filtro de mediana)
    img = img.filter(ImageFilter.MedianFilter(size=3))
    return img

# ======================
# INICIALIZAÇÃO DO OCR
# ======================
ocr = PaddleOCR(use_angle_cls=True, lang='pt', use_gpu=False)

# ======================
# PROCESSAMENTO DAS PÁGINAS
# ======================
all_results = []
print(f"Processando {len(images)} página(s) do PDF...")

# Função utilitária para dividir a imagem em regiões
def split_image_regions(img, n_rows=2, n_cols=2, overlap=0.05):
    width, height = img.size
    regions = []
    row_height = height // n_rows
    col_width = width // n_cols
    for r in range(n_rows):
        for c in range(n_cols):
            left = max(0, int(c * col_width - col_width * overlap))
            upper = max(0, int(r * row_height - row_height * overlap))
            right = min(width, int((c + 1) * col_width + col_width * overlap))
            lower = min(height, int((r + 1) * row_height + row_height * overlap))
            regions.append((left, upper, right, lower))
    return regions

for i, image in enumerate(images):
    print(f"Processando página {i+1}...")
    # Pré-processamento global
    pre_img = preprocess_image(image)

    # Dividir em regiões
    regions = split_image_regions(pre_img, n_rows=2, n_cols=2, overlap=0.08)
    page_data = []
    for idx, (left, upper, right, lower) in enumerate(regions):
        region_img = pre_img.crop((left, upper, right, lower))
        temp_image_path = f'temp_page_{i}_region_{idx}.png'
        region_img.save(temp_image_path, 'PNG')
        result = ocr.ocr(temp_image_path, cls=True)
        os.remove(temp_image_path)
        if result and result[0] is not None:
            for line in result[0]:
                text_info = line[1]
                # Ajustar bounding box para coordenadas da página inteira
                bbox = [
                    [pt[0] + left, pt[1] + upper] if isinstance(pt, (list, tuple)) and len(pt) == 2 else pt
                    for pt in line[0]
                ]
                page_data.append({
                    "text": text_info[0],
                    "confidence": float(text_info[1]),
                    "bounding_box": bbox
                })
    all_results.append({"page": i + 1, "data": page_data})

# ======================
# SALVAR RESULTADO
# ======================
with open(output_json_path, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=4)

print(f"Resultados do OCR salvos em {output_json_path}")
