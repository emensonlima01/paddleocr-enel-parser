# ======================
# IMPORTAÇÕES E CONFIGS
# ======================
import os
import json
import logging
from pathlib import Path # Usar Pathlib para manipulação de caminhos
from typing import List, Dict, Tuple, Any # Adicionar type hints

from dotenv import load_dotenv
from paddleocr import PaddleOCR # type: ignore # Adicionar ignore para libs sem stubs
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
# import numpy as np # Numpy não está sendo usado diretamente, pode ser removido se for dependência apenas do PaddleOCR

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Carregar variáveis do arquivo .env
load_dotenv()

# --- Constantes de Configuração ---
PDF_PATH_STR = os.getenv('PDF_PATH')
if not PDF_PATH_STR:
    logging.error("A variável de ambiente PDF_PATH não está definida.")
    raise ValueError("PDF_PATH não configurado no arquivo .env")

PDF_PATH = Path(PDF_PATH_STR)
if not PDF_PATH.is_file():
    logging.error(f"Arquivo PDF não encontrado em: {PDF_PATH}")
    raise FileNotFoundError(f"Arquivo PDF não encontrado em: {PDF_PATH}")

# O nome do JSON de saída será igual ao do PDF, trocando a extensão por .json
OUTPUT_JSON_PATH = PDF_PATH.with_suffix('.json')

# Caminho relativo ao diretório do script para o poppler
BASE_DIR = Path(__file__).resolve().parent
# Atenção: A estrutura de subdiretórios "layer/poppler/layer/poppler" parece redundante.
# Se for intencional, mantenha. Caso contrário, simplifique.
# Exemplo de caminho simplificado se a estrutura for "layer/poppler-23.11.0/Library/bin":
# POPPLER_PATH = BASE_DIR / "layer" / "poppler-23.11.0" / "Library" / "bin"
# Mantendo o caminho original fornecido:
POPPLER_PATH = BASE_DIR / "layer" / "poppler" / "layer" / "poppler" / "poppler-23.11.0" / "Library" / "bin"

# Configurações de OCR e Imagem
OCR_LANGUAGE = 'pt'
IMAGE_DPI = 400
PREPROCESS_CONTRAST_FACTOR = 2.0
PREPROCESS_BINARIZE_THRESHOLD = 180
PREPROCESS_MEDIAN_FILTER_SIZE = 3
REGION_SPLIT_ROWS = 2
REGION_SPLIT_COLS = 2
REGION_OVERLAP_PERCENTAGE = 0.08 # 8% de sobreposição

# ======================
# FUNÇÕES AUXILIARES
# ======================

def convert_pdf_to_image(pdf_path: Path, poppler_path: Path, first_page: int = 1, last_page: int = 1, dpi: int = IMAGE_DPI) -> List[Image.Image]:
    """Converte páginas de um PDF para uma lista de objetos de imagem PIL."""
    logging.info(f"Convertendo PDF '{pdf_path.name}' para imagem...")
    try:
        images = convert_from_path(
            pdf_path=str(pdf_path), # convert_from_path espera strings
            poppler_path=str(poppler_path),
            first_page=first_page,
            last_page=last_page,
            dpi=dpi
        )
        if not images:
            logging.warning("Nenhuma imagem foi gerada a partir do PDF.")
        return images
    except Exception as e:
        logging.error(f"Erro ao converter PDF para imagem: {e}")
        raise

def preprocess_image(img: Image.Image) -> Image.Image:
    """Aplica pré-processamento a uma imagem para melhorar a qualidade do OCR."""
    logging.debug("Pré-processando imagem...")
    # Converter para escala de cinza
    img = img.convert('L')
    # Aumentar contraste
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(PREPROCESS_CONTRAST_FACTOR)
    # Binarização (threshold)
    img = img.point(lambda x: 0 if x < PREPROCESS_BINARIZE_THRESHOLD else 255, '1')
    # Remover ruído (filtro de mediana)
    img = img.filter(ImageFilter.MedianFilter(size=PREPROCESS_MEDIAN_FILTER_SIZE))
    return img

def split_image_into_regions(img: Image.Image, n_rows: int, n_cols: int, overlap_percentage: float) -> List[Tuple[int, int, int, int]]:
    """Divide a imagem em regiões menores com sobreposição."""
    width, height = img.size
    regions: List[Tuple[int, int, int, int]] = []
    row_height = height // n_rows
    col_width = width // n_cols

    overlap_h = int(row_height * overlap_percentage)
    overlap_w = int(col_width * overlap_percentage)

    for r in range(n_rows):
        for c in range(n_cols):
            left = max(0, c * col_width - (overlap_w if c > 0 else 0))
            upper = max(0, r * row_height - (overlap_h if r > 0 else 0))
            right = min(width, (c + 1) * col_width + (overlap_w if c < n_cols - 1 else 0))
            lower = min(height, (r + 1) * row_height + (overlap_h if r < n_rows - 1 else 0))
            regions.append((left, upper, right, lower))
    return regions

def perform_ocr_on_image_regions(
    image: Image.Image,
    ocr_engine: PaddleOCR,
    page_index: int
) -> List[Dict[str, Any]]:
    """
    Pré-processa uma imagem, divide em regiões, executa OCR em cada região
    e retorna os dados consolidados da página.
    """
    logging.info(f"Processando página {page_index + 1}...")
    pre_processed_img = preprocess_image(image.copy()) # Usar .copy() para evitar modificar a original se necessário

    regions = split_image_into_regions(
        pre_processed_img,
        n_rows=REGION_SPLIT_ROWS,
        n_cols=REGION_SPLIT_COLS,
        overlap_percentage=REGION_OVERLAP_PERCENTAGE
    )

    page_data: List[Dict[str, Any]] = []
    temp_image_dir = BASE_DIR / "temp_ocr_images" # Diretório para imagens temporárias
    temp_image_dir.mkdir(exist_ok=True) # Cria o diretório se não existir

    for i, (left, upper, right, lower) in enumerate(regions):
        region_img = pre_processed_img.crop((left, upper, right, lower))
        temp_image_path = temp_image_dir / f'temp_page_{page_index}_region_{i}.png'

        try:
            region_img.save(temp_image_path, 'PNG')
            logging.debug(f"Realizando OCR na região {i+1} da página {page_index+1}...")
            result = ocr_engine.ocr(str(temp_image_path), cls=True) # ocr espera caminho como string

            if result and result[0] is not None: # Checagem mais robusta
                for line_info in result[0]:
                    # line_info é uma lista [bounding_box, (texto, confiança)]
                    # Ex: [[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], ('texto reconhecido', 0.99)]
                    bounding_box_coords = line_info[0]
                    text, confidence = line_info[1]

                    # Ajustar bounding box para coordenadas da página inteira
                    adjusted_bbox = [
                        [pt[0] + left, pt[1] + upper] for pt in bounding_box_coords
                    ]
                    page_data.append({
                        "text": text,
                        "confidence": float(confidence),
                        "bounding_box": adjusted_bbox
                    })
        except Exception as e:
            logging.error(f"Erro durante OCR na região {temp_image_path}: {e}")
        finally:
            if temp_image_path.exists():
                os.remove(temp_image_path) # Remover imagem temporária

    # Limpar diretório temporário se estiver vazio (opcional)
    if not any(temp_image_dir.iterdir()):
        temp_image_dir.rmdir()

    return page_data

def save_results_to_json(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Salva os resultados do OCR em um arquivo JSON."""
    logging.info(f"Salvando resultados do OCR em '{output_path}'...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info("Resultados salvos com sucesso.")
    except IOError as e:
        logging.error(f"Erro ao salvar o arquivo JSON: {e}")
        raise

# ======================
# FLUXO PRINCIPAL
# ======================
def main():
    """Função principal para executar o pipeline de OCR."""
    logging.info("Iniciando processo de OCR...")

    # CONVERSÃO PDF -> IMAGEM
    try:
        images_from_pdf = convert_pdf_to_image(PDF_PATH, POPPLER_PATH)
    except Exception:
        logging.critical("Falha na conversão do PDF. Encerrando.")
        return # Ou sys.exit(1)

    if not images_from_pdf:
        logging.warning("Nenhuma imagem foi extraída do PDF. Encerrando.")
        return

    # INICIALIZAÇÃO DO OCR
    logging.info(f"Inicializando PaddleOCR com idioma '{OCR_LANGUAGE}'...")
    try:
        ocr_engine = PaddleOCR(use_angle_cls=True, lang=OCR_LANGUAGE, use_gpu=False, show_log=False) # show_log=False para menos verbosidade
    except Exception as e:
        logging.critical(f"Falha ao inicializar o PaddleOCR: {e}")
        return

    # PROCESSAMENTO DAS PÁGINAS
    all_pages_results: List[Dict[str, Any]] = []
    logging.info(f"Processando {len(images_from_pdf)} página(s) do PDF...")

    for i, image in enumerate(images_from_pdf):
        try:
            page_ocr_data = perform_ocr_on_image_regions(image, ocr_engine, page_index=i)
            all_pages_results.append({"page": i + 1, "data": page_ocr_data})
        except Exception as e:
            logging.error(f"Erro ao processar a página {i+1}: {e}. Pulando esta página.")
            all_pages_results.append({"page": i + 1, "data": [], "error": str(e)})


    # SALVAR RESULTADO
    if all_pages_results:
        try:
            save_results_to_json(all_pages_results, OUTPUT_JSON_PATH)
        except Exception:
            logging.critical("Falha ao salvar os resultados. Verifique os logs.")
    else:
        logging.warning("Nenhum resultado de OCR foi gerado para salvar.")

    logging.info("Processo de OCR concluído.")

if __name__ == '__main__':
    main()
