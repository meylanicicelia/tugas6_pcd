# Deteksi Keberadaan Tanda Tangan dengan Thresholding dan Morphology

Mini project Pengolahan Citra Digital. Sistem menentukan **SIGNATURE PRESENT** atau **SIGNATURE ABSENT** pada area tanda tangan pejabat (Dekan dan Rektor) di citra ijazah.

## Alur program
1. **Crop** area tanda tangan (ROI).
2. **Grayscale**.
3. **Thresholding**, tiga metode: global (T=128), Otsu, dan adaptive Gaussian. Hasilnya dibandingkan.
4. **Morphology**: opening (buang bintik noise), lalu closing (sambung goresan putus), lalu hapus komponen kecil (< 40 piksel).
5. **Karakteristik area**: jumlah piksel foreground, rasio terhadap luas ROI, ukuran bounding box, jumlah komponen.
6. **Aturan keputusan** pada hasil Otsu: PRESENT jika
   - piksel foreground ≥ 150,
   - rasio foreground ≥ 0,4% dari luas ROI,
   - lebar bounding box ≥ 60 px dan tinggi ≥ 30 px.

   Jika tidak, ABSENT.

## Struktur repositori
```
src/config.py              # ROI dan semua parameter
src/prepare_dataset.py     # ekstrak citra dari PDF + buat citra tanpa tanda tangan
src/signature_detector.py  # program utama
data/with_signature/       # 9 citra dengan tanda tangan
data/without_signature/    # 9 citra tanpa tanda tangan
results/                   # gambar perbandingan, threshold_sweep.png, summary.csv
ANALISIS.md                # jawaban pertanyaan analisis
requirements.txt
```

## Cara menjalankan
Butuh Python 3.9+.

```bash
git clone https://github.com/meylanicicelia/tugas6_pcd.git
cd tugas6_pcd
python -m venv venv
venv\Scripts\activate            # Windows PowerShell. Linux/Mac: source venv/bin/activate
pip install -r requirements.txt

cd src
python signature_detector.py --with_dir ../data/with_signature --without_dir ../data/without_signature --out ../results
```

Keluaran: tabel hasil di terminal, akurasi, `results/summary.csv`, satu gambar perbandingan per citra dan ROI (`results/<citra>_<roi>.png`), dan `results/threshold_sweep.png`.

Opsi lain (jalankan dari folder `src`):
```bash
# satu citra saja
python signature_detector.py --image ../data/with_signature/faded.png --out ../results

# hanya satu ROI
python signature_detector.py --roi dekan --with_dir ../data/with_signature --without_dir ../data/without_signature --out ../results
```

### Membuat ulang dataset dari PDF (opsional)
Letakkan `IJAZAH_PCD.pdf` di folder proyek, lalu:
```bash
python src/prepare_dataset.py IJAZAH_PCD.pdf
```
Skrip ini mengekstrak 9 citra dari PDF, memutarnya tegak, dan menormalkan lebar menjadi 800 px. Untuk membuat citra **tanpa tanda tangan**, ROI tanda tangan ditimpa potongan kertas kosong dari citra yang sama, sehingga warna, noise, dan blur tetap sama.

### Memakai dokumen sendiri
Letakkan citra di `data/with_signature/` dan `data/without_signature/`, lalu sesuaikan ROI dan ambang di `src/config.py`. Koordinat ROI berlaku pada citra berlebar 800 px (program mengubah ukuran otomatis).

## Data
- 9 citra adalah **satu ijazah yang sama** dengan 9 jenis degradasi: highquality, lowcontrast, blurred, highnoise, lowres, faded, colorshift, jpeg, combined.
- 9 citra tanpa tanda tangan dibuat dari 9 citra itu dengan menghapus tanda tangan Dekan dan Rektor (lihat atas).
- Ijazah memuat data pribadi. Disarankan menjaga repositori ini **private**.

## Hasil
Pengujian: 18 citra x 2 ROI = 36 kasus.

| Metode | Akurasi dengan aturan yang sama |
|---|---|
| Global (T=128) | 19/36 |
| **Otsu (metode utama)** | **36/36** |
| Adaptive | 36/36 |

Piksel foreground pada ROI Dekan (citra bertanda tangan):

| Citra | Global | Otsu | Adaptive | Otsu T |
|---|---|---|---|---|
| highquality | 113 | 3037 | 3330 | 206 |
| lowcontrast | 0 | 2830 | 2546 | 222 |
| blurred | 41 | 2812 | 3102 | 212 |
| highnoise | 93 | 2632 | 3022 | 203 |
| lowres | 86 | 2917 | 3137 | 211 |
| faded | 1005 | 2916 | 2183 | 141 |
| colorshift | 95 | 2877 | 3092 | 203 |
| jpeg | 83 | 2889 | 3136 | 210 |
| combined | 294 | 2782 | 2885 | 165 |

Pada semua 18 citra tanpa tanda tangan, ketiga metode menghasilkan 0 piksel.

Global 19/36 berarti benar pada semua 18 citra ABSENT, tetapi hanya 1 dari 18 kasus PRESENT (`faded`, ROI Dekan). Tinta tanda tangan pada ijazah ini tidak cukup gelap untuk T=128.

## Keterbatasan
- Sembilan citra berasal dari satu dokumen, bukan sembilan dokumen berbeda.
- Citra tanpa tanda tangan dibuat dengan menimpa ROI, jadi areanya sangat bersih (0 piksel). Dokumen nyata yang memang tidak ditandatangani bisa lebih kotor (noda, bekas cap, teks cetak).
- ROI tetap, sehingga posisi tanda tangan yang bergeser perlu penyesuaian `src/config.py`.
- Aturan tidak membedakan tanda tangan dari coretan atau teks cetak yang cukup besar di dalam ROI.

Penjelasan analisis ada di [ANALISIS.md](ANALISIS.md).
