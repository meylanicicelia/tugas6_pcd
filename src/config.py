"""Parameter bersama. Semua koordinat ROI berlaku pada citra yang sudah dinormalisasi lebar 800 px."""
WIDTH = 800

# ROI tanda tangan (x, y, w, h)
ROIS = {
    "dekan":  (492, 372, 214, 92),   # tanda tangan Dekan (kanan bawah)
    "rektor": (100, 396, 225, 68),   # tanda tangan Rektor (kiri bawah)
}
BLANK_ROI = (10, 10, 200, 74)        # kertas kosong, dipakai membuat citra TANPA tanda tangan

# Parameter thresholding
GLOBAL_T = 128                       # nilai threshold global tetap
ADAPTIVE_BLOCK, ADAPTIVE_C = 31, 8   # adaptive Gaussian: ukuran blok & konstanta

# Parameter aturan keputusan
MIN_CONTRAST = 15     # guard Otsu: median latar - rata-rata foreground
MIN_COMP_AREA = 40    # komponen terhubung < nilai ini dianggap noise (piksel)
MIN_PIXELS = 150      # jumlah piksel foreground minimal
MIN_RATIO = 0.004     # foreground / luas ROI minimal
MIN_BBOX_W = 60       # lebar bounding box minimal
MIN_BBOX_H = 30       # tinggi bounding box minimal
