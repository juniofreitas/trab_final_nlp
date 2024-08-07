# Create script that download all pdf file from  url
# Usage: python download_pdfs.py <url> <output_dir>

import requests
import sys
import os
from bs4 import BeautifulSoup


def download_pdfs(url, output_dir):
    # add agent to avoid 403 error
    # headers = {
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.3"
    # }
    # Add support for javascript pages for request

    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    response = requests.get(url)
    print(response.headers)
    soup = BeautifulSoup(response.text, "html.parser")
    # get host name with https
    host = url.split("/")[0] + "//" + url.split("/")[2]

    for link in soup.find_all("a"):
        href = link.get("href")
        if href.endswith(".pdf"):

            pdf_url = href if href.startswith("http") else host + href
            # pdf_url = href
            pdf_name = href.split("/")[-1]
            pdf_path = os.path.join(output_dir, pdf_name)
            print(f"Downloading from {pdf_url}")
            with open(pdf_path, "wb") as f:
                f.write(requests.get(pdf_url).content)
            # print(f"Downloaded {pdf_name} to {pdf_path}")


if __name__ == "__main__":
    url = sys.argv[1]
    output_dir = sys.argv[2]
    download_pdfs(url, output_dir)

# Usage: python download_pdfs.py https://www.example.com/ ./pdfs
# Downloaded file1.pdf to ./pdfs/file1.pdf
