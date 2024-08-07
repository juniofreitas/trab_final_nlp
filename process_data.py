import argparse
import glob
import os
import re
from urllib.parse import unquote


class ProcessData:
    def __init__(self, source: str, dest: str, merge: bool = False) -> None:
        self.source: str = source
        self.dest: str = dest
        self.lfiles: list[str] = []
        self.merge: bool = merge
        self.merge_file: str = "merge_data.txt"
        if not os.path.exists(self.dest):
            os.makedirs(self.dest, exist_ok=True)

    # create func that load files name frmo source folder
    def load_files(self) -> None:
        self.lfiles = [name for name in glob.glob(os.path.join(self.source, "*.txt"))]

    # save list of files preprocessing to dest folder
    def save_files(self, hdata: dict[str, str]) -> None:
        if self.merge:
            merge_data: str = "\n".join(hdata.values())
            with open(os.path.join(self.dest, self.merge_file), "w") as f:
                f.write(merge_data)
        for item in hdata.items():
            with open(os.path.join(self.dest, item[0]), "w") as f:
                f.write(item[1])

    # Cleaning data
    def clean_data(self, data: str) -> str:
        # remove indication of page number
        data = re.sub(r"(PAG\.\d+)\s*\n", "", data)

        # fix paragraph with line break in the middle, union lines in same paragraph
        data = re.sub(
            r"([^\.\;\:\!\?])[ \t]*(?:\r\n\n|\n\n)[ \t]*([a-z\d])",
            r"\1 \2",
            data,
            flags=re.M,
        )
        data = re.sub(r"(\w|\,)[ \t]*(?:\r\n|\n)[ \t]*(\S)", r"\1 \2", data, flags=re.M)
        # Remove blank lines
        data = re.sub(r"\n\s*\n", "\n", data)
        # Remove stranger characters, except for letters, numbers, and punctuations defined in the string.pontuation
        data = re.sub(r"[^\w\s\.,;:\!\?\'\"\(\)\[\]\{\}\-\*\+\=\\\/\<\>]", "", data)
        # Split text in paragraphs and remove lines winth only one word and number
        data = "\n".join(
            [
                line.strip()
                for line in data.split("\n")
                if len(line.split()) > 1 or not re.match(r"^\d+$", line)
            ]
        )
        return data

    # create func that process list text of file and do data cleaning
    def preprocess(self) -> None:
        self.load_files()
        hdata: dict[str, str] = {}
        for file in self.lfiles:
            ufile = unquote(file)
            print(f"Preprocessing data from {ufile}")
            with open(file, "r") as f:
                data: str = f.read()
                data = self.clean_data(data)
                hdata[os.path.basename(ufile)] = data
        self.save_files(hdata)


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Preprocessa os textos extraídos de PDF."
    )
    parser.add_argument(
        "SOURCE",
        nargs=1,
        help="Pasta com os arquivos Texto's!",
        type=str,
    )
    parser.add_argument(
        "DEST",
        nargs=1,
        help="Pasta de destino dos arquivos processados!",
        type=str,
    )
    parser.add_argument(
        "-merge",
        action="store_true",
        help="Se definido, os arquivos processados serão salvos em um único arquivo.",
    )
    args: argparse.Namespace = parser.parse_args()
    folder: str = args.SOURCE[0]
    dest: str = args.DEST[0]
    merge: bool = args.merge
    pd = ProcessData(folder, dest, merge)
    print(f'\nProcessando os arquivos de texto da pasta "{folder} ..."\n')
    pd.preprocess()
    print(f"\nArquivos processados salvos em {dest}\n")

    # pd = ProcessData("./pdfs")
    # file = "RES%2069_2010%20CURSO%20DE%20F%c3%89RIAS.txt"
    # fdata = open(file, "r", encoding="utf-8")
    # print(f"Cleaning data from {file}")
    # data = pd.clean_data(fdata.read())
    # print(data)


if __name__ == "__main__":
    main()
