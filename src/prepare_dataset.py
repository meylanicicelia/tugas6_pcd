"""Menyiapkan dataset dari IJAZAH_PCD.pdf:
 1) ekstrak 9 citra (satu ijazah, 9 jenis degradasi), putar tegak, normalisasi lebar 800 px
    -> data/with_signature/
 2) buat 9 citra TANPA tanda tangan dengan menimpa ROI tanda tangan (Dekan & Rektor)
    memakai potongan kertas kosong dari citra yang sama (sehingga warna, noise, dan blur ikut sama)
    -> data/without_signature/
Pakai: python src/prepare_dataset.py IJAZAH_PCD.pdf"""
import io, os, sys
import cv2, numpy as np
from PIL import Image
from pypdf import PdfReader
import config as C

NAMES = ["highquality", "lowcontrast", "blurred", "highnoise", "lowres",
         "faded", "colorshift", "jpeg", "combined"]          # urutan halaman pada PDF
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def main(pdf):
    os.makedirs(f"{ROOT}/with_signature", exist_ok=True)
    os.makedirs(f"{ROOT}/without_signature", exist_ok=True)
    bx, by, bw, bh = C.BLANK_ROI
    for page, name in zip(PdfReader(pdf).pages, NAMES):
        pil = page.images[0].image.convert("RGB")
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)        # halaman PDF berotasi 90 derajat
        s = C.WIDTH / img.shape[1]
        img = cv2.resize(img, (C.WIDTH, int(img.shape[0] * s)), interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(f"{ROOT}/with_signature/{name}.png", img)

        blank = img[by:by + bh, bx:bx + bw]                    # patch kertas kosong
        nosig = img.copy()
        for x, y, w, h in C.ROIS.values():
            nosig[y:y + h, x:x + w] = cv2.resize(blank, (w, h), interpolation=cv2.INTER_LINEAR)
        cv2.imwrite(f"{ROOT}/without_signature/{name}_nosig.png", nosig)
        print("OK:", name)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "IJAZAH_PCD.pdf")
