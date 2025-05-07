# PaddleOCR Enel Parser

Este projeto realiza a extração de texto (OCR) de faturas da Enel (ou outros documentos PDF similares) utilizando a biblioteca PaddleOCR. O processo inclui pré-processamento avançado de imagem para otimizar a qualidade do reconhecimento de texto.

## Sumário

- [Sobre o PaddleOCR](#sobre-o-paddleocr)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Como Usar](#como-usar)
  - [Pré-requisitos](#pré-requisitos)
  - [Configuração do Ambiente](#configuração-do-ambiente)
  - [Execução](#execução)
- [Detalhes do Fluxo de Processamento](#detalhes-do-fluxo-de-processamento)
  - [1. Conversão do PDF em Imagem](#1-conversão-do-pdf-em-imagem)
  - [2. Pré-processamento da Imagem](#2-pré-processamento-da-imagem)
  - [3. Divisão da Imagem em Regiões](#3-divisão-da-imagem-em-regiões)
  - [4. OCR e Agregação dos Resultados](#4-ocr-e-agregação-dos-resultados)
  - [5. Exportação dos Resultados](#5-exportação-dos-resultados)
- [Explicação das Funções e Lógica do Código](#explicação-das-funções-e-lógica-do-código)
- [Observações e Pontos de Melhoria](#observações-e-pontos-de-melhoria)
- [Licença](#licença)

---

## Sobre o PaddleOCR

[PaddleOCR](https://paddlepaddle.github.io/PaddleOCR/main/en/index.html) é uma biblioteca open-source de Reconhecimento Óptico de Caracteres (OCR) desenvolvida pela Baidu, baseada no framework PaddlePaddle. Ela disponibiliza modelos pré-treinados para diversos idiomas, incluindo o português, e oferece suporte eficiente para detecção e reconhecimento de texto em imagens com alta precisão.

**Principais características do PaddleOCR:**
- Suporte a múltiplos idiomas e scripts.
- Modelos otimizados para execução em CPU e GPU.
- Integração simplificada com projetos Python.
- Comunidade ativa e documentação abrangente.

- **Repositório Oficial:** [https://github.com/PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- **Documentação:** [https://paddlepaddle.github.io/PaddleOCR/main/en/index.html](https://paddlepaddle.github.io/PaddleOCR/main/en/index.html)

> O PaddleOCR é mantido pela equipe do PaddlePaddle/Baidu e pela comunidade open-source. Recomenda-se consultar a documentação oficial para informações detalhadas sobre instalação, configuração de modelos e exemplos avançados.

---

## Funcionalidades Principais

- **Conversão de PDF para Imagem**: Converte a primeira página de um arquivo PDF em uma imagem de alta resolução (DPI 400 por padrão), crucial para capturar textos pequenos e detalhes finos.
- **Pré-processamento de Imagem**: Aplica técnicas como conversão para escala de cinza, aumento de contraste, binarização e filtro de mediana para remover ruídos, melhorando significativamente a qualidade da imagem para o OCR.
- **Divisão Inteligente de Página**: Segmenta a imagem da página em múltiplas regiões menores, com uma leve sobreposição entre elas. Esta técnica aumenta a precisão do OCR, especialmente em documentos com leiautes complexos, tabelas ou campos de texto próximos.
- **Extração de Dados com PaddleOCR**: Utiliza o PaddleOCR configurado para o idioma português para extrair o texto, o nível de confiança de cada reconhecimento e as coordenadas da caixa delimitadora (bounding box) de cada fragmento de texto.
- **Saída Estruturada em JSON**: Salva os resultados completos do OCR em um arquivo JSON bem formatado. O nome do arquivo JSON será o mesmo do PDF de entrada (ex: `fatura.pdf` -> `fatura.json`). Isso facilita a análise posterior, integração com outros sistemas e a utilização dos dados extraídos.

---

## Como Usar

### Pré-requisitos

- **Python 3.8+** (Python 3.10 é recomendado)
- Gerenciador de pacotes Pip
- Ambiente virtual (recomendado para isolar dependências)
- **Poppler**: Necessário para a conversão de PDF para imagem. O projeto inclui uma versão para Windows. Para outros sistemas operacionais, pode ser necessário instalar separadamente.

### Configuração do Ambiente

1.  **Clone o repositório (se aplicável) ou baixe os arquivos.**

2.  **Crie e ative um ambiente virtual:**
    No terminal, navegue até o diretório do projeto e execute:
    ```bash
    python -m venv .venv
    ```
    Para ativar (Windows PowerShell):
    ```powershell
    .venv\Scripts\Activate.ps1
    ```
    Para ativar (Linux/macOS):
    ```bash
    source .venv/bin/activate
    ```

3.  **Instale as dependências Python:**
    ```bash
    pip install paddleocr pdf2image Pillow python-dotenv numpy
    ```
    *(Observação: `numpy` é frequentemente uma dependência do `paddleocr` ou `Pillow`)*

4.  **Verifique o Poppler:**
    O script espera encontrar o Poppler no caminho `layer/poppler/layer/poppler/poppler-23.11.0/Library/bin` relativo ao `main.py`. Certifique-se de que essa estrutura existe ou ajuste o `POPPLER_PATH` no `main.py` conforme necessário.

### Execução

1.  **Prepare o arquivo PDF**: Coloque o arquivo PDF que deseja processar no diretório raiz do projeto (ou em qualquer local e ajuste o caminho no `.env`).

2.  **Configure o arquivo `.env`**:
    Crie um arquivo chamado `.env` na raiz do projeto com o seguinte conteúdo, substituindo `nome_do_seu_arquivo.pdf` pelo nome real do seu PDF:
    ```env
    PDF_PATH=nome_do_seu_arquivo.pdf
    ```

3.  **Execute o script**:
    No terminal, com o ambiente virtual ativado, execute:
    ```bash
    python main.py
    ```
    O script processará o PDF e salvará os resultados em um arquivo JSON com o mesmo nome do PDF de entrada, mas com a extensão `.json` (ex: `nome_do_seu_arquivo.json`), no mesmo diretório do PDF.

---

## Detalhes do Fluxo de Processamento

O script segue um pipeline robusto para extrair texto de documentos PDF:

### 1. Conversão do PDF em Imagem
Utilizando a biblioteca `pdf2image` e o backend Poppler, a primeira página do PDF especificado é convertida para um objeto de imagem da biblioteca Pillow. A conversão é feita com uma alta resolução (DPI 400 por padrão) para preservar detalhes do texto.

### 2. Pré-processamento da Imagem
A função `preprocess_image` aplica uma série de filtros para otimizar a imagem para OCR:
    1.  **Escala de Cinza**: Converte a imagem para tons de cinza, eliminando informações de cor que podem ser ruído para o OCR.
    2.  **Aumento de Contraste**: Realça a diferença entre o texto e o fundo.
    3.  **Binarização**: Transforma a imagem em preto e branco puro, com base em um limiar (threshold), facilitando a segmentação do texto.
    4.  **Filtro de Mediana**: Remove pequenos ruídos ("sal e pimenta") e suaviza as bordas do texto.

### 3. Divisão da Imagem em Regiões
A função `split_image_into_regions` divide a imagem pré-processada em um grid (por padrão, 2x2 = 4 regiões). Uma sobreposição configurável é aplicada entre as regiões adjacentes para garantir que nenhum texto seja perdido nas bordas das divisões. Processar regiões menores pode melhorar a precisão do OCR, especialmente em documentos densos.

### 4. OCR e Agregação dos Resultados
Para cada região:
    - A região é salva temporariamente como um arquivo PNG.
    - O motor PaddleOCR (`ocr.ocr()`) é invocado para extrair texto, confiança e coordenadas da caixa delimitadora.
    - As coordenadas da caixa delimitadora são ajustadas para refletir sua posição na imagem original da página inteira.
    - Os dados de todas as regiões são agregados para formar o resultado completo da página.
    - As imagens temporárias das regiões são removidas.

### 5. Exportação dos Resultados
Os dados extraídos de todas as páginas processadas (atualmente apenas a primeira) são compilados em uma lista. Esta lista é então salva em um arquivo JSON. O nome do arquivo de saída é derivado do nome do arquivo PDF de entrada (ex: `fatura.pdf` se torna `fatura.json`). O JSON inclui o número da página, o texto extraído, a confiança e as coordenadas da caixa delimitadora para cada detecção.

---

## Explicação das Funções e Lógica do Código (no `main.py` melhorado)

- **Constantes de Configuração**: Parâmetros como caminhos, DPI, configurações de pré-processamento e divisão de regiões são definidos como constantes no início do script para fácil ajuste.
- **`convert_pdf_to_image()`**: Isola a lógica de conversão de PDF.
- **`preprocess_image()`**: Contém as etapas de melhoria da qualidade da imagem.
- **`split_image_into_regions()`**: Gerencia a divisão da imagem em partes menores com sobreposição.
- **`perform_ocr_on_image_regions()`**: Orquestra o pré-processamento, divisão, OCR por região e coleta de resultados para uma única página.
- **`save_results_to_json()`**: Responsável por escrever os dados extraídos no arquivo JSON.
- **`main()`**: Função principal que controla o fluxo de execução, desde o carregamento da configuração até o salvamento dos resultados, incluindo logging e tratamento básico de erros.
- **Logging**: O módulo `logging` é usado para fornecer feedback sobre o progresso e quaisquer problemas encontrados.

---

## Observações e Pontos de Melhoria

- **Caminho do Poppler**: Definido de forma relativa, mas a estrutura aninhada `layer/poppler/layer/poppler` pode ser um erro de digitação e poderia ser simplificada para `layer/poppler-XYZ/Library/bin`. Verifique e ajuste se necessário.
- **Ajustes de OCR**: A eficácia do OCR pode variar. Experimente com os parâmetros em `preprocess_image` (contraste, limiar de binarização, tamanho do filtro) e `split_image_into_regions` (número de linhas/colunas, porcentagem de sobreposição) para otimizar para diferentes tipos de documentos.
- **Múltiplas Páginas**: O script atualmente processa apenas a primeira página do PDF (`first_page=1`, `last_page=1`). Pode ser estendido para processar múltiplas páginas ou o documento inteiro, ajustando os parâmetros `first_page` e `last_page` na função `convert_pdf_to_image` e iterando sobre as imagens resultantes.
- **GPU para PaddleOCR**: Se uma GPU compatível estiver disponível e configurada, mudar `use_gpu=False` para `use_gpu=True` no `main.py` pode acelerar significativamente o processo de OCR.
- **Tratamento de Erros Avançado**: O tratamento de erros pode ser expandido para ser mais granular ou para tentar diferentes estratégias de recuperação.
- **Modularidade**: Para projetos maiores, as funções poderiam ser organizadas em classes ou módulos separados.
- **Teste**: Adicionar testes unitários e de integração para garantir a robustez das funções.
- **Interface de Usuário**: Para facilitar o uso por não desenvolvedores, uma interface gráfica simples (ex: com Tkinter, PyQt) ou uma interface de linha de comando mais elaborada (ex: com `argparse` ou `Typer`) poderia ser desenvolvida.

---

## Licença

Este projeto é disponibilizado para fins educacionais e de demonstração. Sinta-se à vontade para adaptá-lo e utilizá-lo conforme suas necessidades.
