# paddleocr-enel-parser

Este projeto realiza a extração de texto (OCR) de faturas da Enel (ou outros PDFs similares) utilizando o PaddleOCR, com pré-processamento de imagem para maximizar a qualidade do reconhecimento.

## Sobre o PaddleOCR

[PaddleOCR](https://paddlepaddle.github.io/PaddleOCR/main/en/index.html) é uma biblioteca open source para reconhecimento óptico de caracteres (OCR) baseada no framework PaddlePaddle, mantido pela Baidu. Ela oferece modelos prontos para diversos idiomas, incluindo português, e suporta detecção e reconhecimento de texto em imagens de forma eficiente e com alta precisão.

Principais características do PaddleOCR:
- Suporte a múltiplos idiomas e scripts.
- Modelos otimizados para CPU e GPU.
- Fácil integração em projetos Python.
- Comunidade ativa e documentação detalhada.

Repositório oficial: https://github.com/PaddlePaddle/PaddleOCR
Documentação: https://paddlepaddle.github.io/PaddleOCR/main/en/index.html

O PaddleOCR é mantido pela equipe do PaddlePaddle/Baidu e pela comunidade open source. Recomenda-se sempre consultar a documentação oficial para detalhes de instalação, configuração de modelos e exemplos avançados.

O fluxo completo inclui: conversão do PDF em imagem de alta resolução, pré-processamento (binarização, contraste, remoção de ruído), divisão da página em regiões menores, execução do OCR em cada região e exportação dos resultados em JSON.

## Funcionalidades
- Converte a primeira página de um PDF em imagem com alta resolução (DPI 400), garantindo que textos pequenos e detalhes sejam capturados.
- Aplica pré-processamento na imagem (binarização, aumento de contraste e remoção de ruído) para melhorar a qualidade do OCR.
- Divide a página em regiões menores (com sobreposição) para aumentar a precisão do reconhecimento, especialmente em documentos com tabelas ou campos próximos.
- Utiliza o PaddleOCR com idioma português para extrair textos, níveis de confiança e posições (bounding box).
- Salva o resultado do OCR em um arquivo JSON estruturado, facilitando análise e integração.

## Sumário

- [Sobre o PaddleOCR](#sobre-o-paddleocr)
- [Funcionalidades](#funcionalidades)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Usar](#como-usar)
  - [Pré-requisitos](#pré-requisitos)
  - [Configuração do Ambiente](#configuração-do-ambiente)
  - [Execução](#execução)
- [Detalhes do Fluxo](#detalhes-do-fluxo)
- [Observações](#observações)
- [Licença](#licença)

---

## Como Usar

### Pré-requisitos

- **Python 3.10** (recomendado)
- Ambiente virtual dedicado

### Configuração do Ambiente

1. Instale o Python 3.10:
   [Download Python 3.10](https://www.python.org/downloads/release/python-3100/)
   (Marque "Add Python to PATH" na instalação)

2. No terminal, crie e ative o ambiente virtual:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Atualize o pip (opcional):
   ```powershell
   python -m pip install --upgrade pip
   ```

4. Instale as dependências:
   ```powershell
   pip install paddleocr pdf2image pillow numpy python-dotenv
   ```

5. Certifique-se de que o Poppler está em `layer/poppler/layer/poppler/poppler-23.11.0/Library/bin` (já incluso no repositório para Windows).

### Execução

1. Coloque o PDF desejado na raiz do projeto.
2. Configure o arquivo `.env` na raiz do projeto:
   ```
   PDF_PATH=56164154-959566847213.pdf
   ```

3. Execute o script:
   ```powershell
   python main.py
   ```
   O resultado será salvo em um arquivo `.json` com o mesmo nome do PDF.

## Passo a Passo Detalhado

### 1. Conversão do PDF em Imagem
O script utiliza `pdf2image.convert_from_path` para converter a primeira página do PDF em uma imagem PNG de alta resolução (DPI 400). Isso é fundamental para garantir que textos pequenos e detalhes sejam capturados pelo OCR.

### 2. Função `preprocess_image(img)`
Esta função realiza o pré-processamento da imagem para maximizar a qualidade do OCR:
1. Converte a imagem para escala de cinza (reduz ruído de cor).
2. Aumenta o contraste (deixa o texto mais destacado).
3. Binariza a imagem (preto e branco), facilitando a separação do texto do fundo.
4. Aplica filtro de mediana para remover pequenos ruídos e sujeiras.
Esse pré-processamento é essencial para melhorar a nitidez do texto e reduzir interferências de fundo.

### 3. Função `split_image_regions(img, n_rows=2, n_cols=2, overlap=0.08)`
Divide a imagem da página em 4 regiões (2 linhas x 2 colunas), com uma pequena sobreposição entre elas. Isso aumenta a chance de capturar textos que ficam próximos às margens ou entre colunas, comuns em faturas e boletos.

### 4. OCR e Montagem do Resultado
Para cada região, a imagem é salva temporariamente, processada pelo PaddleOCR e o resultado é ajustado para as coordenadas da página inteira. Todos os textos reconhecidos, junto com suas posições e níveis de confiança, são salvos em um arquivo JSON estruturado.

### 5. Exportação dos Resultados
O resultado do OCR é salvo em `resultado_ocr.json`, contendo uma lista de textos extraídos, suas posições (bounding box) e o nível de confiança de cada detecção.

## Explicação das Funções e Lógica do Código

- **Pré-processamento:** Melhora a qualidade da imagem para o OCR, tornando o texto mais legível e reduzindo ruídos.
- **Divisão em regiões:** Aumenta a cobertura do OCR, evitando perda de informações em áreas de borda ou colunas.
- **PaddleOCR:** Utilizado com idioma português, reconhece textos e retorna suas posições e confiabilidade.
- **Estrutura modular:** Fácil de adaptar para outros tipos de documentos ou ajustes de pré-processamento.

## Observações
- O caminho do Poppler é definido de forma relativa ao script, facilitando o uso em diferentes máquinas.
- O OCR pode ser ajustado alterando o pré-processamento ou a divisão de regiões.
- O projeto está focado em faturas da Enel, mas pode ser adaptado para outros PDFs.
- O pré-processamento pode ser ajustado conforme o tipo de documento (por exemplo, mudando o threshold da binarização).
- O PaddleOCR está configurado para português (`lang='pt'`), mas pode ser alterado para outros idiomas.
- O resultado em JSON pode ser usado para buscas, análises ou integração com outros sistemas.
- O projeto está focado em faturas da Enel, mas pode ser adaptado para outros PDFs e cenários de OCR.

## Licença
Este projeto é apenas para fins educacionais e de demonstração.
