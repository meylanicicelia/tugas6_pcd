"""Deteksi keberadaan tanda tangan.
Pipeline: crop ROI -> grayscale -> thresholding (Global, Otsu, Adaptive) -> perbandingan
-> morphology (opening, closing) -> karakteristik area -> aturan PRESENT / ABSENT."""
import argparse, csv, glob, os
import cv2, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C


# ---------------------------------------------------------------- 1. crop & grayscale
def load(path):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    if img.shape[1] != C.WIDTH:
        s = C.WIDTH / img.shape[1]
        img = cv2.resize(img, (C.WIDTH, int(img.shape[0] * s)), interpolation=cv2.INTER_CUBIC)
    return img


def crop_roi(img, roi):
    x, y, w, h = roi
    return img[y:y + h, x:x + w]


def to_gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


# ---------------------------------------------------------------- 2. thresholding
def threshold_methods(gray):
    """Tiga metode. Hasil: tinta = putih (255)."""
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, g = cv2.threshold(blur, C.GLOBAL_T, 255, cv2.THRESH_BINARY_INV)                 # global
    t_otsu, o = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)    # Otsu
    # Otsu selalu membelah histogram, termasuk pada area kosong yang hanya berisi noise.
    # Jika tinta tidak cukup lebih gelap dari latar, anggap tidak ada foreground.
    if cv2.countNonZero(o) > 0 and np.median(blur) - blur[o > 0].mean() < C.MIN_CONTRAST:
        o = np.zeros_like(o)
    a = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                              cv2.THRESH_BINARY_INV, C.ADAPTIVE_BLOCK, C.ADAPTIVE_C)  # adaptive
    return {"Global": g, "Otsu": o, "Adaptive": a}, t_otsu


# ---------------------------------------------------------------- 3. morphology
def morphology(binary):
    """Opening (hapus bintik noise) lalu closing (sambung goresan yang putus)."""
    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, k_open)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, k_close)
    return opened, closed


def remove_small(binary, min_area=C.MIN_COMP_AREA):
    n, lab, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    out = np.zeros_like(binary)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            out[lab == i] = 255
    return out


# ---------------------------------------------------------------- 4. karakteristik area
def analyze(mask):
    px = int(cv2.countNonZero(mask))
    pts = cv2.findNonZero(mask)
    if pts is None:
        return dict(pixels=0, ratio=0.0, bw=0, bh=0, n_comp=0)
    _, _, bw, bh = cv2.boundingRect(pts)
    n, *_ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    return dict(pixels=px, ratio=px / mask.size, bw=bw, bh=bh, n_comp=n - 1)


# ---------------------------------------------------------------- 5. aturan keputusan
def decide(m):
    """PRESENT jika jumlah piksel, rasio, dan ukuran bounding box foreground memenuhi ambang."""
    ok = (m["pixels"] >= C.MIN_PIXELS and m["ratio"] >= C.MIN_RATIO
          and m["bw"] >= C.MIN_BBOX_W and m["bh"] >= C.MIN_BBOX_H)
    return "SIGNATURE PRESENT" if ok else "SIGNATURE ABSENT"


# ---------------------------------------------------------------- pipeline + visualisasi
def process(img, roi, stem, save_dir):
    roi_img = crop_roi(img, roi)
    gray = to_gray(roi_img)
    masks, t_otsu = threshold_methods(gray)
    results, final = {}, {}
    for name, m in masks.items():
        opened, closed = morphology(m)
        clean = remove_small(closed)
        final[name] = (m, opened, closed, clean)
        results[name] = analyze(clean)
    label = decide(results["Otsu"])          # metode utama = Otsu

    fig, ax = plt.subplots(4, 4, figsize=(12, 6.5))
    ax[0, 0].imshow(cv2.cvtColor(roi_img, cv2.COLOR_BGR2RGB)); ax[0, 0].set_title("crop ROI", fontsize=8)
    ax[0, 1].imshow(gray, cmap="gray", vmin=0, vmax=255); ax[0, 1].set_title("grayscale", fontsize=8)
    ax[0, 2].axis("off"); ax[0, 3].axis("off")
    ax[0, 2].text(0, .5, f"{stem}\nOtsu T={t_otsu:.0f}\n{label}", fontsize=9, va="center")
    for r, name in enumerate(["Global", "Otsu", "Adaptive"], start=1):
        for c, (im, ttl) in enumerate(zip(final[name], ["threshold", "opening", "closing", "hasil akhir"])):
            ax[r, c].imshow(im, cmap="gray", vmin=0, vmax=255)
            extra = f" ({results[name]['pixels']} px)" if c == 3 else ""
            ax[r, c].set_title(f"{name}: {ttl}{extra}", fontsize=8)
    for a in ax.ravel():
        a.set_xticks([]); a.set_yticks([])
    plt.tight_layout()
    fig.savefig(os.path.join(save_dir, f"{stem}.png"), dpi=65)
    plt.close(fig)
    return label, results, t_otsu


def threshold_sweep(img, roi, save_dir):
    """Demonstrasi threshold terlalu rendah / terlalu tinggi (analisis)."""
    blur = cv2.GaussianBlur(to_gray(crop_roi(img, roi)), (5, 5), 0)
    ts = [40, 100, 160, 200, 235]
    fig, ax = plt.subplots(1, len(ts), figsize=(14, 2.6))
    for a, t in zip(ax, ts):
        _, b = cv2.threshold(blur, t, 255, cv2.THRESH_BINARY_INV)
        a.imshow(b, cmap="gray", vmin=0, vmax=255); a.axis("off")
        a.set_title(f"T={t}  ({cv2.countNonZero(b)} px)", fontsize=9)
    plt.tight_layout()
    fig.savefig(os.path.join(save_dir, "threshold_sweep.png"), dpi=80)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description="Deteksi keberadaan tanda tangan (PRESENT/ABSENT)")
    p.add_argument("--with_dir", default="data/with_signature")
    p.add_argument("--without_dir", default="data/without_signature")
    p.add_argument("--image", help="uji satu citra saja")
    p.add_argument("--roi", choices=list(C.ROIS), help="batasi ke satu ROI (dekan/rektor)")
    p.add_argument("--out", default="results")
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rois = {a.roi: C.ROIS[a.roi]} if a.roi else C.ROIS

    if a.image:
        items = [(a.image, None)]
    else:
        items = [(f, "SIGNATURE PRESENT") for f in sorted(glob.glob(os.path.join(a.with_dir, "*.png")))]
        items += [(f, "SIGNATURE ABSENT") for f in sorted(glob.glob(os.path.join(a.without_dir, "*.png")))]

    rows, total, correct = [], 0, 0
    per_method = {"Global": 0, "Otsu": 0, "Adaptive": 0}
    print(f"{'Citra':<22}{'ROI':<8}{'OtsuT':>6}{'Global':>8}{'Otsu':>7}{'Adapt':>7}{'bw':>5}{'bh':>5}  {'Prediksi':<19}Hasil")
    for path, truth in items:
        img = load(path)
        base = os.path.splitext(os.path.basename(path))[0]
        for rname, roi in rois.items():
            label, res, t = process(img, roi, f"{base}_{rname}", a.out)
            o = res["Otsu"]
            ok = ""
            if truth:
                total += 1
                correct += label == truth
                ok = "OK" if label == truth else "SALAH"
                for m in per_method:
                    per_method[m] += decide(res[m]) == truth
            print(f"{base:<22}{rname:<8}{t:>6.0f}{res['Global']['pixels']:>8}{o['pixels']:>7}"
                  f"{res['Adaptive']['pixels']:>7}{o['bw']:>5}{o['bh']:>5}  {label:<19}{ok}")
            rows.append([base, rname, truth, label, round(t), res["Global"]["pixels"], o["pixels"],
                         res["Adaptive"]["pixels"], round(o["ratio"], 4), o["bw"], o["bh"], o["n_comp"]])

    with open(os.path.join(a.out, "summary.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["image", "roi", "ground_truth", "prediction", "otsu_T", "px_global", "px_otsu",
                    "px_adaptive", "otsu_ratio", "bbox_w", "bbox_h", "n_components"])
        w.writerows(rows)
    if total:
        print(f"\nAkurasi Otsu (metode utama): {correct}/{total} = {100 * correct / total:.1f}%")
        print("Akurasi tiap metode dengan aturan yang sama:",
              ", ".join(f"{k}={v}/{total}" for k, v in per_method.items()))
    first = items[0][0]
    threshold_sweep(load(first), list(rois.values())[0], a.out)


if __name__ == "__main__":
    main()
