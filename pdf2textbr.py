"""
Created on Thu Mar 28 07:30:00 2018
@author: Junio Freitas (u4uz)
@email: juniofreitas@gmail.com
Descrição: esta classe processa arquivos pdf e extrai o texto deste arquivo.
Parametros: nome do arquivo e diretorio onde se encontra o arquivo pdf
"""

import re
import glob
import os
from subprocess import Popen, PIPE
from PIL import Image, ImageEnhance
import pytesseract as ocr


class pdf2textbr:
    """
    Esta classe implementa um metodo de extracao de texto de um arquivo PDF.
    Há dois tipos de arquivos PDF que esta classe processa:
    1 - PDF Digitalizado: gerado a partir da digitalização do documento original e
    seu conteúdo é todo formado por imagens;
    2 - PDF Padrão: contém texto puro e outros tipos de objetos.
    No caso 1 o texto só pode ser extraído usando técnicas de OCR que extrai texto
    de imagem. No caso 2 é possível extrair o texto diretamento do PDF.
    Para extrair o texto do PDF primeiramente a classe tenta extriar o texto
    diretamente e, senão conseguir, tenta extrair via OCR.
    Para realizar esse processo a classe utiliza duas ferramentas externas:
    - Tesseract: ferramenta que realiza o OCR de imagens
    - Xpdf: conjunto de ferramenta que extrai diversas informações de um arquivo
    em pdf, dentre essas, extrai texto.
    """

    # Constantes
    DEST = "result"
    EXEC1 = "pdftoppm"  # "pdftopng"
    EXEC2 = "pdftotext"
    DPI = "300"
    PREFIX = "res"
    ARGS1 = [EXEC1, "-png"]
    ARGS2 = [EXEC2, "-raw"]
    SIZE = 7016, 4961
    CONFIGS = "--oem 2"

    def __init__(self, f, src, lang="eng"):
        self.file = f
        self.source = src
        self.lang = lang
        self.prefix = os.path.splitext(os.path.basename(self.file))[0]
        self.dest = self.DEST + "-" + self.source
        self.npag = 0
        Image.MAX_IMAGE_PIXELS = None
        if not os.path.exists(self.dest):
            os.makedirs(self.dest, exist_ok=True)

    def __del__(self):
        self.file = self.source = self.dest = self.prefix = None

    def __str__(self):
        return "pdf2textbr<{},{},{}>".format(self.file, self.source, self.dest)

    # Monta comando da execucao do extrator de imagens do pdf
    def monta_comando(self, args, ext=""):
        nargs = args[:]
        nargs.append(self.file)
        nargs.append(os.path.join(self.dest, self.prefix + ext))
        return nargs

    # Processa comando baseado nos argumentos
    def processa_comando(self, args):
        proc = Popen(args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        data, err = proc.communicate()
        return err

    # Carrega lista de imagens geradas em memoria
    def carrega_imagem_gerada(self):
        return [
            Image.open(f)
            for f in sorted(
                glob.glob(os.path.join(self.dest, "{}*.png".format(self.prefix)))
            )
        ]

    # Carrega lista de nomes das imagens geradas
    def carrega_nome_imagem_gerada(self):
        return [
            namef
            for namef in sorted(
                glob.glob(os.path.join(self.dest, "{}*.png".format(self.prefix)))
            )
        ]

    # Carrega o arquivos texto gerado
    def carrega_arquivo_gerado(self):
        lfile = [
            f for f in glob.glob(os.path.join(self.dest, "{}.txt".format(self.prefix)))
        ]
        if len(lfile) > 0:
            with open(lfile[0], "r") as content_file:
                content = content_file.read()
            return content.strip()
        return None

    # Carrega imagem do disco em memoria
    def carrega_imagem(self, namef):
        return Image.open(namef)

    # Salva imagem da memoria em disco
    def salva_imagem(self, img, namef):
        img.save(namef)

    # Extrai imagens de um arquivo pdf digitalizado
    def extrai_imagens(self):
        args = self.monta_comando(self.ARGS1)
        err = self.processa_comando(args)
        if len(err) > 0:
            print(
                '***Atenção: ao processar a imagem {} retornou-se "{}"'.format(
                    self.file, err
                )
            )
        lnamesimg = self.carrega_nome_imagem_gerada()
        return lnamesimg

    # Extrai o texto de um arquivo pdf padrao
    def extrai_texto(self):
        args = self.monta_comando(self.ARGS2, ".txt")
        err = self.processa_comando(args)
        if len(err) > 0:
            print(
                '***Atenção: ao processar a imagem {} retornou-se "{}"'.format(
                    self.file, err
                )
            )
        content = self.carrega_arquivo_gerado()
        return content

    # Faz tratamento da imagem para melhora o processo de extracao do texto
    def melhora_imagem(self, img):
        # out = img.convert('RGB')
        out = img.resize(self.SIZE, Image.ANTIALIAS)
        out = out.convert("L")
        eo = ImageEnhance.Contrast(out)
        out = eo.enhance(2.0)
        eo = ImageEnhance.Sharpness(out)
        out = eo.enhance(2.0)
        return out

    # Faz uma limpeza basica do texto extraido
    def limpa_texto(self, text):
        ctxt = re.sub(" +", " ", text)  # etc...
        return ctxt

    # Faz o tratamento por pagina do arquivo de texto gerado
    def trata_texto(self, content):
        pages = content.split("\f")
        for i, pg in enumerate(pages):
            # pg = self.limpa_texto(pg)
            pg = "PAG.{}\n\n".format(i + 1) + pg
            pages[i] = pg
        if len(pages) > 0 and len(pages[-1]) <= 1:
            pages = pages[:-1]
        self.npg = len(pages)
        return pages

    # Salva o texto extraido da imagem em arquivo
    def salva_texto_imagem(self, text, pg=1):
        name = self.prefix + ".txt"
        ot = "w" if pg == 1 else "a"
        with open(os.path.join(self.dest, name), ot, encoding="utf-8") as textfile:
            textfile.write("PAG.{}\n\n".format(pg) + text + "\n\n")

    # Salva o texto formatado extraido em arquivo
    def salva_texto(self, pages):
        with open(
            os.path.join(self.dest, "{}.txt".format(self.prefix)), "w"
        ) as textfile:
            [textfile.write("{}\n\n".format(pg)) for pg in pages]

    # faz o trabalho do OCR
    def ocr_text(self):
        lnimgs = self.extrai_imagens()
        self.npg = len(lnimgs)
        for i, nimg in enumerate(lnimgs):
            pg = i + 1
            print("...página {}".format(pg))
            img = self.carrega_imagem(nimg)
            # nimg = self.melhora_imagem(img)
            try:
                text = ocr.image_to_string(img, lang=self.lang, config=self.CONFIGS)
            except ValueError:
                return False
            text = self.limpa_texto(text)
            self.salva_texto_imagem(text, pg)
            os.remove(img.filename)
            img = nimg = None
        return len(lnimgs) > 0

    # Faz o trabalho de extrair o texto do PDF
    def pdf_text(self):
        content = self.extrai_texto()
        if content:
            pages = self.trata_texto(content)
            print("...numeros paginas: {}".format(len(pages)))
            self.salva_texto(pages)
        return content is not None and len(content) > 1

    # Realiza a extracao em si, independente se é pdf padrao ou digitalizado
    def extracao(self):
        res = self.pdf_text()
        if not res or self.npg == 1:
            res = self.ocr_text()
        return res
