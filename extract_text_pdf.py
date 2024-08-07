import argparse
import time
import concurrent.futures
from pdf2textbr import pdf2textbr
import os
import glob


# create class that extracts text from pdf
class ExtractTextPdf:
    def __init__(self, folder: str):
        if not os.path.exists(folder):
            raise (f"***O diretorio {folder} não existe!")
        self.folder: str = folder

    def run_parallel(self):
        all_start_time: float = time.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            lfiles: list[str] = [
                name for name in glob.glob(os.path.join(self.folder, "*.pdf"))
            ]
            lsource: list[str] = [self.folder for i in range(len(lfiles))]
            print(f"Numero de arquivos a serem processados: {len(lfiles)}\n")
            for file, res in zip(lfiles, executor.map(self.process, lfiles, lsource)):
                print(f"\n-> Processando arquivo: {file}. Resultado:{res}")
        print(f"\n TEMPO TOTAL: {(time.time() - all_start_time)} segundos.\nOK!")

    def process(self, file: str, source: str):
        res: bool = False
        try:
            start_time: float = time.time()
            p2t: pdf2textbr = pdf2textbr(file, source, "por")
            res = p2t.extracao()
            print(f"...TEMPO: {(time.time() - start_time)} segundos ")
        except Exception as e:
            print(f"***Erro ao processar o arquivo {file}. Erro={e}")
        return res


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Extrator de textos de arquivos PDF."
    )
    parser.add_argument(
        "FOLDER",
        nargs=1,
        help="Pasta com os arquivos PDF's!",
        type=str,
    )
    args: argparse.Namespace = parser.parse_args()
    folder: str = args.FOLDER[0]
    print(f'\nProcessando os arquivos PDFs da pasta "{folder}"\n')
    extractor = ExtractTextPdf(folder)
    extractor.run_parallel()


# Usage
if __name__ == "__main__":
    main()
