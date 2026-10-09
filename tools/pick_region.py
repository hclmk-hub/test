"""PDFの1ページを表示し、氏名欄をマウスで囲んで座標を config.json に保存するツール。

使い方:
    python tools/pick_region.py sample.pdf [--page 1] [--config config.json]

操作:
    - ドラッグで氏名欄を囲む(やり直しは再ドラッグ)
    - 「保存」ボタンで config.json に書き込む
座標はページ全体に対する割合(0〜1)で保存するため、解像度が違うPDFでも使える。
"""
import argparse
import json
import tkinter as tk
from tkinter import messagebox

import pymupdf  # PyMuPDF
from PIL import Image, ImageTk

MAX_VIEW = 900  # 表示する画像の最大の高さ(px)


def render_page(pdf_path, page_no):
    doc = pymupdf.open(pdf_path)
    if not 1 <= page_no <= len(doc):
        raise SystemExit(f"ページ番号は 1〜{len(doc)} で指定してください")
    page = doc[page_no - 1]
    zoom = MAX_VIEW / page.rect.height
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--config", default="config.json")
    args = ap.parse_args()

    img = render_page(args.pdf, args.page)
    w, h = img.size

    root = tk.Tk()
    root.title("氏名欄をドラッグで囲んでください")
    canvas = tk.Canvas(root, width=w, height=h)
    canvas.pack()
    photo = ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, anchor="nw", image=photo)

    state = {"start": None, "rect": None, "box": None}
    label = tk.Label(root, text="未選択")
    label.pack()

    def clamp(v, hi):
        return max(0, min(v, hi))

    def on_press(e):
        state["start"] = (clamp(e.x, w), clamp(e.y, h))

    def on_drag(e):
        if state["rect"]:
            canvas.delete(state["rect"])
        x0, y0 = state["start"]
        state["rect"] = canvas.create_rectangle(
            x0, y0, clamp(e.x, w), clamp(e.y, h), outline="red", width=2
        )

    def on_release(e):
        x0, y0 = state["start"]
        x1, y1 = clamp(e.x, w), clamp(e.y, h)
        left, right = sorted((x0, x1))
        top, bottom = sorted((y0, y1))
        if right - left < 5 or bottom - top < 5:
            return
        state["box"] = [round(left / w, 4), round(top / h, 4),
                        round(right / w, 4), round(bottom / h, 4)]
        label.config(text=f"left/top/right/bottom = {state['box']}")

    def save():
        if not state["box"]:
            messagebox.showwarning("未選択", "先に氏名欄を囲んでください")
            return
        try:
            with open(args.config, encoding="utf-8") as f:
                cfg = json.load(f)
        except FileNotFoundError:
            cfg = {}
        cfg["name_region"] = state["box"]
        with open(args.config, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("保存しました", f"{args.config} に書き込みました")

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    tk.Button(root, text="保存", command=save).pack(pady=4)
    root.mainloop()


if __name__ == "__main__":
    main()
