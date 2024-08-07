import argparse
import glob
import os
import textwrap
import pandas as pd
import time
from tqdm import tqdm
import langchain
from langchain_openai import OpenAI
import re


class ConstructInstructionDataset:
    def __init__(self, source: str, dest: str) -> None:
        self.source: str = source
        self.dest: str = dest
        self.hdata: dict[str, str] = {}
        self.llm = OpenAI(model="gpt-3.5-turbo-instruct")
        if not os.path.exists(self.dest):
            os.makedirs(self.dest, exist_ok=True)
        # create dest file csv only with header
        df = pd.DataFrame(columns=["Instruction", "Response"])
        df.to_csv(os.path.join(self.dest, "instructions_dataset.csv"), index=False)

    # Load file list to hdata
    def load_files(self) -> None:
        lfiles: list[str] = [
            name for name in glob.glob(os.path.join(self.source, "*.txt"))
        ]
        for file in lfiles:
            with open(file, "r") as f:
                self.hdata[os.path.basename(file)] = f.read()

    # save instructions and responses in dest folder
    def save_dataset(self, instructions: list[str], responses: list[str]) -> None:
        df = pd.DataFrame({"Instruction": instructions, "Response": responses})
        df.to_csv(
            os.path.join(self.dest, "instructions_dataset.csv"),
            index=False,
            mode="a",
            header=not os.path.exists(
                os.path.join(self.dest, "instructions_dataset.csv")
            ),
        )

    # Return merge one ou more data file from hdata
    def merge_data(self, fro: int, to: int) -> str:
        to = len(self.hdata) if to == -1 or to > len(self.hdata) else to
        return " ".join(list(self.hdata.values())[fro:to])

    # split data file using textwrap to limit the number of characters
    def split_data(self, data: str, limit: int = 4000) -> list[str]:
        return textwrap.wrap(data, limit)

    # counting the number of words in a text
    def count_words(self, text: str) -> int:
        return len(text.split())

    # Return the number of instruction based in the number of words
    def get_num_instruction(self, words: int) -> int:
        if 0 < words <= 100:
            return 1
        elif 100 < words <= 500:
            return 2
        elif 500 < words <= 1000:
            return 3
        elif 1000 < words <= 1500:
            return 5
        elif 1500 < words <= 2048:
            return 5
        else:
            return 6

    def extract_instruction_response_pairs(
        self, string: str
    ) -> tuple[list[str], list[str]]:
        """
        Extracts pairs of instructions and responses from a JSON-formatted string.

        Parameters:
            - json_string (str): A string containing JSON-formatted instruction and response pairs.

        Returns:
            - instructions (list): A list of extracted instructions.
            - responses (list): A list of extracted responses corresponding to the instructions.
        """

        pattern: str = r'{"Instruction": "(.*?)", "Response": "(.*?)"}'
        # Use re.findall to extract matches
        matches: list[any] = re.findall(pattern, string)
        # Extract lists of "Instruction" and "Response"
        instructions: str = [match[0] for match in matches]
        responses: str = [match[1] for match in matches]
        return instructions, responses

    def get_prompt(self, focus: str, describe: str, num_inst: int = 5) -> str:
        return f"""### Instruções: Baseado no arquivo {focus} com informações sobre a legislação acadêmica de Graduação da Universidade Federal do
            Amazonas (UFAM) abaixo, gere {num_inst} pares de respostas detalhadas com instruções.
            Certifique-se de que a instrução-resposta esteja no formato json:\n\n
            ### Exemplo: {{"Instruction": "a instrução", "Response": "a resposta"}}\n\n
            ### Descrição:{describe}\n\n
            ### Resposta:"""

    def construct_instruction(self) -> None:
        self.load_files()
        All_instructions: list[str] = []
        All_reponses: list[str] = []
        start: float = time.time()
        for file, data in self.hdata.items():
            print(f"Processando arquivo: {file}")
            splited_data: list[str] = self.split_data(data, 2048)
            for i, part_data in enumerate(splited_data):
                numinstr: int = self.get_num_instruction(self.count_words(part_data))
                print(
                    f"Processando parte {i+1} de {len(splited_data)}. Num instruções: {numinstr}"
                )
                for _ in range(25):
                    focus: str = f"{file}{i+1}"
                    describe: str = part_data
                    prompt: str = self.get_prompt(focus, describe, numinstr)
                    generated_text: str = self.llm(prompt)
                    ins, res = self.extract_instruction_response_pairs(generated_text)
                    All_instructions.extend(ins)
                    All_reponses.extend(res)
            self.save_dataset(All_instructions, All_reponses)
            All_instructions.clear()
            All_reponses.clear()
        print("\n\n===Time: {} seconds===".format(time.time() - start))


def main():
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Gera a base de instruções para o fine-tuning do LLM."
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
        help="Pasta de destino da base de instruções!",
        type=str,
    )
    args: argparse.Namespace = parser.parse_args()
    source: str = args.SOURCE[0]
    dest: str = args.DEST[0]
    cid = ConstructInstructionDataset(source, dest)
    print(f'\nGerando a base de instruções a partir dos arquivos de "{source} ..."\n')
    cid.construct_instruction()
    print(f"\nBase de instruções geradas e salva em {dest}\n")


if __name__ == "__main__":
    main()
