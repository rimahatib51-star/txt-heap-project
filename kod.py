

import re
import sys
import os

# ═══════════════════════════════════════════════════════════
#  RENK PALETİ
# ═══════════════════════════════════════════════════════════

class C:
    RST  = "\033[0m"
    BOLD = "\033[1m"
    DIM  = "\033[2m"
    ITAL = "\033[3m"

    BLK  = "\033[30m";  RED  = "\033[91m";  GRN  = "\033[92m"
    YLW  = "\033[93m";  BLU  = "\033[94m";  MAG  = "\033[95m"
    CYN  = "\033[96m";  WHT  = "\033[97m"

    ORG  = "\033[38;5;214m";  PRP  = "\033[38;5;135m"
    PNK  = "\033[38;5;213m";  LME  = "\033[38;5;154m"
    TEL  = "\033[38;5;51m";   SKY  = "\033[38;5;117m"
    GLD  = "\033[38;5;220m";  CRL  = "\033[38;5;203m"

    BG_BLK  = "\033[40m";   BG_RED  = "\033[41m";  BG_GRN  = "\033[42m"
    BG_YLW  = "\033[43m";   BG_BLU  = "\033[44m";  BG_MAG  = "\033[45m"
    BG_CYN  = "\033[46m";   BG_WHT  = "\033[47m"
    BG_DRK  = "\033[48;5;234m"
    BG_PRP  = "\033[48;5;55m"
    BG_NVY  = "\033[48;5;17m"
    BG_TEL  = "\033[48;5;23m"

def p(color: str, text: str) -> str:
    return f"{color}{text}{C.RST}"

def clr_clear():
    """Terminal'i temizle (isteğe bağlı)."""
    pass   # os.system("cls" if os.name == "nt" else "clear")


# ═══════════════════════════════════════════════════════════
#  HEAP NODE
# ═══════════════════════════════════════════════════════════

class HeapNode:
    """
    Her düğüm bir kelimeyi ve frekansını tutar.

    Karşılaştırma 2 anahtara göre yapılır:
      • Birincil  : ilk harf  (A → Z,  küçük harf normalize)
      • İkincil   : -frekans  (büyük frekans = küçük key → öne geçer)
    """
    __slots__ = ("word", "freq")

    def __init__(self, word: str, freq: int = 1):
        self.word = word
        self.freq = freq

    def key(self) -> tuple:
        return (self.word[0].lower(), -self.freq)

    def __lt__(self, other: "HeapNode") -> bool:
        return self.key() < other.key()

    def __eq__(self, other: "HeapNode") -> bool:
        return self.key() == other.key()

    def __repr__(self) -> str:
        return f"{self.word}({self.freq})"


# ═══════════════════════════════════════════════════════════
#  DUAL-KEY MIN-HEAP
# ═══════════════════════════════════════════════════════════

class DualKeyHeap:
    """
    İki anahtarlı Min-Heap.
    Dahili dizi + konum haritası ile O(log n) güncelleme.
    sift_up / sift_down elle yazılmıştır.
    """

    def __init__(self):
        self._heap: list[HeapNode] = []
        self._pos:  dict[str, int] = {}   # kelime → dizi indeksi

    # ── Yardımcılar ───────────────────────────────────────────────────────

    def _swap(self, i: int, j: int):
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]
        self._pos[self._heap[i].word] = i
        self._pos[self._heap[j].word] = j

    def _sift_up(self, i: int):
        while i > 0:
            parent = (i - 1) // 2
            if self._heap[i] < self._heap[parent]:
                self._swap(i, parent)
                i = parent
            else:
                break

    def _sift_down(self, i: int):
        n = len(self._heap)
        while True:
            s = i
            l, r = 2 * i + 1, 2 * i + 2
            if l < n and self._heap[l] < self._heap[s]: s = l
            if r < n and self._heap[r] < self._heap[s]: s = r
            if s != i:
                self._swap(i, s)
                i = s
            else:
                break

    # ── Ana İşlemler ──────────────────────────────────────────────────────

    def insert_or_update(self, word: str):
        """
        Kelime heap'te varsa frekansını +1 artır, heap özelliğini koru.
        Yoksa yeni düğüm ekle.
        """
        if word in self._pos:
            i = self._pos[word]
            self._heap[i].freq += 1
            self._sift_up(i)
            self._sift_down(self._pos[word])
        else:
            node = HeapNode(word, 1)
            self._heap.append(node)
            i = len(self._heap) - 1
            self._pos[word] = i
            self._sift_up(i)

    def pop(self) -> "HeapNode | None":
        if not self._heap:
            return None
        if len(self._heap) == 1:
            node = self._heap.pop()
            del self._pos[node.word]
            return node
        self._swap(0, len(self._heap) - 1)
        node = self._heap.pop()
        del self._pos[node.word]
        if self._heap:
            self._sift_down(0)
        return node

    def snapshot(self) -> list[HeapNode]:
        return list(self._heap)

    def __len__(self)   -> int:  return len(self._heap)
    def is_empty(self)  -> bool: return len(self._heap) == 0


# ═══════════════════════════════════════════════════════════
#  HEAP AĞACI GÖRSELLEŞTİRME  —  canvas tabanlı, tam hizalı
#
#  Fikir: her düğüme sabit bir "slot" genişliği ver.
#  Slot genişliği seviyeye göre belirlenir:
#    • yaprak seviyesi: NODE_W + H_PAD
#    • bir üst seviye : 2 × yaprak_slot
#    • ...
#  Böylece her düğüm tam olarak kendi torunlarının ortasına gelir
#  ve / \\ çizgileri mükemmel hizalanır.
# ═══════════════════════════════════════════════════════════

_NW      = 14    # düğüm etiketi görsel genişliği  "[ankara(4) ]"
_H_PAD   = 2     # yaprak düğümler arası minimum boşluk
_MAX_LVL = 99    # tüm seviyeleri göster (dinamik hesap _render_tree içinde)

# ── Düğüm etiketi rengi ───────────────────────────────────────────────────

def _node_color(freq: int, is_root: bool, is_new: bool) -> str:
    if is_root: return C.BG_TEL + C.BLK + C.BOLD
    if is_new:  return C.BG_DRK + C.LME + C.BOLD
    return (C.BG_DRK + C.CRL + C.BOLD if freq >= 7 else
            C.BG_DRK + C.RED + C.BOLD if freq >= 5 else
            C.BG_DRK + C.ORG + C.BOLD if freq == 4 else
            C.BG_DRK + C.YLW + C.BOLD if freq == 3 else
            C.BG_DRK + C.GRN + C.BOLD if freq == 2 else
            C.BG_DRK + C.CYN + C.BOLD)

def _border_color(freq: int, is_root: bool, is_new: bool) -> str:
    if is_root: return C.GLD  + C.BOLD
    if is_new:  return C.LME  + C.BOLD
    return (C.CRL + C.BOLD if freq >= 7 else
            C.RED + C.BOLD if freq >= 5 else
            C.ORG + C.BOLD if freq == 4 else
            C.YLW + C.BOLD if freq == 3 else
            C.GRN + C.BOLD if freq == 2 else
            C.CYN + C.BOLD)

def _fmt_node(nd: "HeapNode", is_root: bool, is_new: bool) -> tuple[str, str, str]:
    """
    Döndür: (top_line, mid_line, bot_line)
    Her satır görsel olarak _NW karakter genişliğinde.
    """
    inner   = f" {nd.word}({nd.freq}) "[:_NW - 2].center(_NW - 2)
    bc      = _border_color(nd.freq, is_root, is_new)
    fc      = _node_color(nd.freq, is_root, is_new)
    dash    = "─" * (_NW - 2)
    top = f"{bc}┌{dash}┐{C.RST}"
    mid = f"{bc}│{fc}{inner}{C.RST}{bc}│{C.RST}"
    bot = f"{bc}└{dash}┘{C.RST}"
    return top, mid, bot


# ── Canvas: karakter ızgarası ─────────────────────────────────────────────

class Canvas:
    """Sabit boyutlu karakter ızgarası; üzerine metin ve çizgi yaz, sonra yazdır."""
    def __init__(self, rows: int, cols: int):
        self._rows = rows
        self._cols = cols
        # Her hücre: (plain_char, color_prefix)
        self._plain  = [[" "] * cols for _ in range(rows)]
        self._colors = [[""]  * cols for _ in range(rows)]

    def put(self, row: int, col: int, text: str, color: str = ""):
        """text'i (renksiz) col'dan başlayarak row satırına yaz."""
        for i, ch in enumerate(text):
            c2 = col + i
            if 0 <= row < self._rows and 0 <= c2 < self._cols:
                self._plain[row][c2]  = ch
                self._colors[row][c2] = color

    def put_colored(self, row: int, col: int,
                    text: str, color: str):
        self.put(row, col, text, color)

    def render(self) -> list[str]:
        lines = []
        for r in range(self._rows):
            out    = ""
            cur_c  = ""
            for c2 in range(self._cols):
                nc = self._colors[r][c2]
                ch = self._plain[r][c2]
                if nc != cur_c:
                    if cur_c:
                        out += C.RST
                    if nc:
                        out += nc
                    cur_c = nc
                out += ch
            if cur_c:
                out += C.RST
            lines.append(out.rstrip())
        # Sondaki boş satırları kaldır
        while lines and not lines[-1].strip():
            lines.pop()
        return lines


# ── Ağaç çizimi ───────────────────────────────────────────────────────────

def _render_tree(nodes: list["HeapNode"], new_word: str):
    """
    Heap'teki TÜM düğümleri canvas üzerinde ikili ağaç olarak çiz.
    Her düğüm kutulu, her seviye ortaya hizalı, / \\ bağlantıları tam.
    """
    import math
    n = len(nodes)
    if n == 0:
        print(p(C.DIM, "    (boş heap)"))
        return

    # Gerçek seviye sayısını hesapla
    total_levels = math.floor(math.log2(n)) + 1   # 1-indexed

    LEAF_SLOT = _NW + _H_PAD          # yaprak seviyesi slot genişliği = 16
    LEFT      = 10                     # sol kenar (etiket alanı)

    # Canvas boyutları
    # Yaprak seviyesindeki toplam genişlik = 2^(total_levels-1) * LEAF_SLOT
    leaf_count = 1 << (total_levels - 1)
    canvas_w   = LEFT + leaf_count * LEAF_SLOT + 4
    canvas_h   = total_levels * 4      # 3 satır kutu + 1 satır bağlantı

    cvs = Canvas(canvas_h, canvas_w)

    idx = 0
    for lv in range(total_levels):
        count     = 1 << lv
        end       = min(idx + count, n)
        lvl_nodes = nodes[idx:end]

        # Bu seviyede her düğümün slot genişliği
        slot_w = (leaf_count >> lv) * LEAF_SLOT   # = LEAF_SLOT * 2^(L-1-lv)

        # Canvas satır numaraları
        row_top  = lv * 4
        row_mid  = lv * 4 + 1
        row_bot  = lv * 4 + 2
        row_conn = lv * 4 + 3

        # Seviye etiketi (orta satıra)
        cvs.put(row_mid, 2, f"L{lv} ▸", C.DIM)

        for k, nd in enumerate(lvl_nodes):
            heap_idx   = idx + k
            is_root    = (heap_idx == 0)
            is_new     = (nd.word == new_word.lower())

            # Slot başlangıcı ve kutu konumu
            slot_x   = LEFT + k * slot_w
            box_x    = slot_x + (slot_w - _NW) // 2
            center_x = box_x + _NW // 2

            bc = _border_color(nd.freq, is_root, is_new)
            fc = _node_color(nd.freq, is_root, is_new)
            inner = f" {nd.word}({nd.freq}) "[:_NW - 2].center(_NW - 2)
            dash  = "─" * (_NW - 2)

            # Kutuyu canvas'a yaz
            cvs.put(row_top, box_x,          f"┌{dash}┐",  bc)
            cvs.put(row_mid, box_x,          "│",           bc)
            cvs.put(row_mid, box_x + 1,      inner,         fc)
            cvs.put(row_mid, box_x + _NW-1,  "│",           bc)
            cvs.put(row_bot, box_x,          f"└{dash}┘",  bc)

            # Bağlantı çizgileri (son seviye değilse)
            if lv < total_levels - 1:
                li = 2 * heap_idx + 1
                ri = 2 * heap_idx + 2
                if li < n:
                    cvs.put(row_conn, center_x - 2, "/",  C.DIM)
                if ri < n:
                    cvs.put(row_conn, center_x + 2, "\\", C.DIM)

        idx = end

    # Canvas'ı terminale yazdır
    for line in cvs.render():
        print("  " + line)


def print_heap_tree(step: int, word: str, nodes: list["HeapNode"]):
    """Adım başlığı + canvas tabanlı ağacı yazdır."""
    W          = 72
    step_badge = p(C.BG_PRP + C.WHT + C.BOLD, f"  ADIM {step:<3}")
    arrow      = p(C.ORG    + C.BOLD,          "  ▶  ")
    word_badge = p(C.GLD    + C.BOLD,          f"{word.upper():<14}")
    size_info  = p(C.DIM,                       f"  heap boyutu: {len(nodes)}")
    div        = p(C.DIM,                       "  " + "─" * W)

    print()
    print(f"  {step_badge}{arrow}{word_badge}{size_info}")
    print(div)
    print()
    _render_tree(nodes, word)
    print()
    print(div)
    print()


# ═══════════════════════════════════════════════════════════
#  DOSYA OKUMA  (hata yoksa geri dön, yoksa None döndür)
# ═══════════════════════════════════════════════════════════

def try_read_words(filepath: str) -> "list[str] | None":
    """
    Dosyayı okumayı dener.
    Başarılıysa kelime listesi döndürür.
    Hata varsa None döndürür (sys.exit ÇAĞIRMAZ).
    """
    filepath = filepath.strip().strip('"').strip("'")

    if not os.path.exists(filepath):
        return None
    if not os.path.isfile(filepath):
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, "r", encoding="latin-1") as f:
                text = f.read()
        except Exception:
            return None
    except Exception:
        return None

    words = [w.lower() for w in re.findall(r"[a-zA-Z]+", text) if w]
    return words if words else []


# ═══════════════════════════════════════════════════════════
#  BANNER
# ═══════════════════════════════════════════════════════════

def print_banner():
    lines = [
        r"  ██╗  ██╗███████╗ █████╗ ██████╗ ",
        r"  ██║  ██║██╔════╝██╔══██╗██╔══██╗",
        r"  ███████║█████╗  ███████║██████╔╝",
        r"  ██╔══██║██╔══╝  ██╔══██║██╔═══╝ ",
        r"  ██║  ██║███████╗██║  ██║██║     ",
        r"  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ",
    ]
    gradient = [C.TEL, C.CYN, C.SKY, C.BLU, C.PRP, C.MAG]
    print()
    for i, line in enumerate(lines):
        print(p(gradient[i % len(gradient)] + C.BOLD, line))

    sub = "  ══════  Dual-Key Heap  │  Kelime Frekans Sayacı  ══════"
    print(p(C.DIM, sub))
    print()


# ═══════════════════════════════════════════════════════════
#  DOSYA YOLU GİRİŞİ  (döngülü, kullanıcı dostu)
# ═══════════════════════════════════════════════════════════

def get_filepath(from_args: "str | None") -> tuple[str, list[str]]:
    """
    Geçerli bir dosya yolu ve kelime listesi elde edene kadar sorar.
    Komut satırı argümanı varsa önce onu dener.
    """
    tip_line = (
        p(C.DIM, "  ╔═ İPUCU ══════════════════════════════════════════╗\n") +
        p(C.DIM, "  ║ ") + p(C.YLW, " Tam yol girin") +
        p(C.DIM, "  → ") + p(C.WHT, "C:\\Belgeler\\metin.txt") +
        p(C.DIM, "                  ║\n") +
        p(C.DIM, "  ║ ") + p(C.YLW, " Aynı klasörde") +
        p(C.DIM, " → ") + p(C.WHT, "ornek.txt") +
        p(C.DIM, "                           ║\n") +
        p(C.DIM, "  ╚══════════════════════════════════════════════════╝")
    )

    attempts = 0

    # Komut satırı argümanını dene
    if from_args:
        result = try_read_words(from_args)
        if result is not None:
            return from_args.strip(), result
        print()
        print(p(C.RED + C.BOLD,
                f"  ✗  '{from_args}' bulunamadı veya okunamadı."))

    # Döngü: geçerli yol alınana kadar sor
    while True:
        attempts += 1

        if attempts == 1:
            print(tip_line)
            print()

        prompt = (
            p(C.CYN + C.BOLD, "  📂 TXT dosyasının yolunu girin") +
            p(C.DIM, " ▶ ")
        )
        raw = input(prompt).strip()

        if not raw:
            print(p(C.YLW, "  ⚠  Boş giriş. Lütfen bir dosya yolu yazın.\n"))
            continue

        # Sadece harf girilmişse (dosya uzantısı yok gibi görünüyor)
        if not raw.endswith(".txt") and "." not in os.path.basename(raw):
            print(
                p(C.YLW + C.BOLD, f"\n  ⚠  '{raw}' bir dosya yolu gibi görünmüyor.\n") +
                p(C.DIM,   "     Lütfen ") +
                p(C.WHT,   ".txt uzantılı") +
                p(C.DIM,   " bir dosya yolu girin.\n") +
                p(C.DIM,   "     Örnek: ") +
                p(C.GRN,   "ornek.txt") +
                p(C.DIM,   "  veya  ") +
                p(C.GRN,   "C:\\Klasör\\dosya.txt\n")
            )
            continue

        result = try_read_words(raw)

        if result is None:
            print(
                p(C.RED + C.BOLD, f"\n  ✗  '{raw}' dosyası bulunamadı!\n") +
                p(C.DIM,          "     Dosyanın var olduğundan ve yolun doğru olduğundan emin olun.\n")
            )
            continue

        if len(result) == 0:
            print(
                p(C.YLW + C.BOLD, f"\n  ⚠  '{raw}' dosyası okundu ama hiç kelime bulunamadı.\n") +
                p(C.DIM,          "     Dosyanın boş olmadığını ve İngilizce karakter içerdiğini kontrol edin.\n")
            )
            continue

        # Başarılı
        print()
        print(p(C.GRN + C.BOLD, "  ✔  Dosya başarıyla okundu!"))
        print(p(C.DIM,           f"     Yol    : ") + p(C.CYN, raw))
        print(p(C.DIM,           f"     Token  : ") +
              p(C.YLW + C.BOLD,   str(len(result))) +
              p(C.DIM,            " kelime"))
        print()
        return raw, result


# ═══════════════════════════════════════════════════════════
#  FREKANS ÇUBUĞU
# ═══════════════════════════════════════════════════════════

def freq_bar(freq: int, max_freq: int, width: int = 22) -> str:
    filled = round((freq / max_freq) * width) if max_freq else 0
    bar    = "█" * filled + "░" * (width - filled)
    col    = (C.CRL  if freq == max_freq        else
              C.RED  if freq >= max_freq * 0.75 else
              C.ORG  if freq >= max_freq * 0.55 else
              C.YLW  if freq >= max_freq * 0.35 else
              C.GRN  if freq >= max_freq * 0.15 else C.TEL)
    return f"{col}{bar}{C.RST}"


# ═══════════════════════════════════════════════════════════
#  SONUÇ TABLOSU
# ═══════════════════════════════════════════════════════════

LETTER_COLORS = [
    C.TEL, C.CYN, C.SKY, C.GRN, C.LME,
    C.YLW, C.GLD, C.ORG, C.CRL, C.RED,
    C.PNK, C.MAG, C.PRP, C.BLU
]

def print_results(results: list[HeapNode], filepath: str):
    if not results:
        print(p(C.RED, "  Sonuç bulunamadı."))
        return

    max_freq    = max(nd.freq for nd in results)
    total       = sum(nd.freq for nd in results)
    unique      = len(results)
    W           = 72   # tablo genişliği (karakter)

    BPP = C.BG_NVY   # tablo arka planı

    def box(ch: str) -> str:
        return p(BPP + C.DIM, ch)

    def boxrow(inner: str) -> str:
        return f"{box('║')}{inner}{box('║')}"

    # ── Başlık ────────────────────────────────────────────────────────────
    print()
    print(box("╔" + "═" * (W - 2) + "╗"))

    title = p(BPP + C.CYN + C.BOLD, f"{'KELIME FREKANS RAPORU':^{W-2}}")
    print(boxrow(title))

    fname = os.path.basename(filepath)
    sub   = p(BPP + C.DIM, f"{'📄  ' + fname:^{W-2}}")
    print(boxrow(sub))

    print(box("╠" + "═" * (W - 2) + "╣"))

    hdr = (p(BPP + C.DIM,  f"  {'№':<4}") +
           p(BPP + C.WHT + C.BOLD, f"{'KELİME':<20}") +
           p(BPP + C.DIM,  f"{'FREKANS':>8}") +
           p(BPP + C.DIM,  f"{'ORAN':>7}  ") +
           p(BPP + C.DIM,  f"{'DAĞILIM':<24}"))
    print(boxrow(hdr))
    print(box("╠" + "═" * (W - 2) + "╣"))
    print(boxrow(p(BPP, " " * (W - 2))))

    # ── Satırlar ──────────────────────────────────────────────────────────
    cur_letter = None
    rank       = 1
    col_idx    = 0

    for nd in results:
        first = nd.word[0].upper()

        # Harf grubu değişti
        if first != cur_letter:
            if cur_letter is not None:
                sep_line = p(BPP + C.DIM, "  " + "·" * (W - 4) + "  ")
                print(boxrow(sep_line))

            lc         = LETTER_COLORS[col_idx % len(LETTER_COLORS)]
            col_idx   += 1
            cur_letter = first

            grp = (p(BPP + lc + C.BOLD, f"  ◈  {first}  ") +
                   p(BPP + C.DIM,        "─" * (W - 12)))
            print(boxrow(grp))

        # Frekans rengi
        pct = (nd.freq / total) * 100
        if nd.freq == max_freq:
            fcol = C.CRL + C.BOLD
        elif nd.freq >= max_freq * 0.75:
            fcol = C.RED
        elif nd.freq >= max_freq * 0.5:
            fcol = C.ORG
        elif nd.freq >= max_freq * 0.25:
            fcol = C.YLW
        else:
            fcol = C.GRN

        bar = freq_bar(nd.freq, max_freq)

        row = (p(BPP + C.DIM,        f"  {rank:<4}") +
               p(BPP + C.WHT + C.BOLD, f"{nd.word:<20}") +
               p(BPP + fcol,           f"{nd.freq:>8}") +
               p(BPP + C.DIM,         f"{pct:>6.1f}%  ") +
               p(BPP,                  bar))
        print(boxrow(row))
        rank += 1

    # ── Alt özet ──────────────────────────────────────────────────────────
    print(boxrow(p(BPP, " " * (W - 2))))
    print(box("╠" + "═" * (W - 2) + "╣"))

    s1 = p(BPP + C.DIM, "  Toplam (tekrarlı) : ") + p(BPP + C.YLW + C.BOLD, f"{total:<8}")
    s2 = p(BPP + C.DIM, "  Benzersiz : ")         + p(BPP + C.CYN + C.BOLD, f"{unique:<8}")
    s3 = p(BPP + C.DIM, "  En yüksek : ")         + p(BPP + C.CRL + C.BOLD, f"{max_freq}")
    print(boxrow(s1 + s2 + s3))

    print(box("╚" + "═" * (W - 2) + "╝"))
    print()


# ═══════════════════════════════════════════════════════════
#  ANA PROGRAM
# ═══════════════════════════════════════════════════════════

def main():
    print_banner()

    # 1 ── Dosya yolu al (döngülü, hata toleranslı)
    arg      = sys.argv[1] if len(sys.argv) >= 2 else None
    filepath, words = get_filepath(arg)

    # 2 ── Adım adım gösterim tercihi
    q = (p(C.MAG + C.BOLD, "  ?  ") +
         p(C.WHT, "Heap adımlarını görmek ister misiniz? ") +
         p(C.DIM, "[e / h]: "))
    show_steps = input(q).strip().lower() in ("e", "evet", "y", "yes", "1", "")
    print()

    # 3 ── Heap oluştur
    heap = DualKeyHeap()

    if show_steps:
        div = p(C.DIM, "  " + "─" * 64)
        print(div)

    for step, word in enumerate(words, 1):
        heap.insert_or_update(word)
        if show_steps:
            print_heap_tree(step, word, heap.snapshot())

    if show_steps:
        print(p(C.DIM, "  " + "─" * 64))
        print()

    # 4 ── Sonuçları çıkar (heap'i boşalt, listeye al)
    results: list[HeapNode] = []
    while not heap.is_empty():
        results.append(heap.pop())

    # 5 ── Mod seç: Tümünü göster  mi  yoksa  kelime ara mı?
    print()
    mod_q = (
        p(C.BG_DRK + C.DIM, "  ┌─────────────────────────────────────────┐\n") +
        p(C.BG_DRK,          "  │  " +
          p(C.CYN + C.BOLD,  "1") + p(C.WHT, "  Tüm kelimeleri göster          ") +
          p(C.BG_DRK + C.DIM, "│\n") +
          p(C.BG_DRK,         "  │  ") +
          p(C.YLW + C.BOLD,  "2") + p(C.WHT, "  Belirli bir kelime ara          ") +
          p(C.BG_DRK + C.DIM, "│\n") +
          p(C.BG_DRK + C.DIM, "  └─────────────────────────────────────────┘"))
    )
    print(mod_q)
    print()

    mod = input(
        p(C.MAG + C.BOLD, "  ▶ Seçiminiz ") + p(C.DIM, "[1 / 2]: ")
    ).strip()
    print()

    if mod == "2":
        # ── Kelime Arama Modu ─────────────────────────────────────────────
        # Arama için dict hazırla (O(1) erişim)
        word_map: dict[str, HeapNode] = {nd.word: nd for nd in results}
        total_all = sum(nd.freq for nd in results)

        while True:
            query = input(
                p(C.CYN + C.BOLD, "  🔍 Kelime girin") +
                p(C.DIM, " (çıkmak için boş bırak) ▶ ")
            ).strip().lower()

            if not query:
                print(p(C.DIM, "\n  Arama tamamlandı.\n"))
                break

            print()
            if query in word_map:
                nd  = word_map[query]
                pct = (nd.freq / total_all) * 100
                bar = freq_bar(nd.freq, max(n.freq for n in results), width=30)
                W   = 52

                BPP = C.BG_NVY
                def box(ch): return p(BPP + C.DIM, ch)
                def boxrow(inner): return f"{box('║')}{inner}{box('║')}"

                print(box("╔" + "═" * (W - 2) + "╗"))
                print(boxrow(p(BPP + C.GLD + C.BOLD,
                               f"  🔎  Arama Sonucu: '{query.upper()}'  ".ljust(W - 2))))
                print(box("╠" + "═" * (W - 2) + "╣"))
                print(boxrow(p(BPP, " " * (W - 2))))

                r1 = (p(BPP + C.DIM,       "  Kelime     : ") +
                      p(BPP + C.WHT + C.BOLD, f"{nd.word}"))
                print(boxrow(r1))

                r2 = (p(BPP + C.DIM,       "  Frekans    : ") +
                      p(BPP + C.CRL + C.BOLD, f"{nd.freq}  kez"))
                print(boxrow(r2))

                r3 = (p(BPP + C.DIM,       "  Oran       : ") +
                      p(BPP + C.YLW + C.BOLD, f"%{pct:.1f}"))
                print(boxrow(r3))

                r4 = p(BPP + C.DIM, "  Dağılım    : ") + p(BPP, bar)
                print(boxrow(r4))

                print(boxrow(p(BPP, " " * (W - 2))))
                print(box("╚" + "═" * (W - 2) + "╝"))

            else:
                # Benzer kelimeleri bul
                similar = [nd for nd in results
                           if nd.word.startswith(query[0])
                           and abs(len(nd.word) - len(query)) <= 3][:5]

                print(p(C.RED + C.BOLD,
                        f"  ✗  '{query}' kelimesi dosyada bulunamadı."))
                if similar:
                    print(p(C.DIM, "\n  Benzer kelimeler:"))
                    for nd in similar:
                        print(p(C.YLW, f"     • {nd.word}") +
                              p(C.DIM, f"  ({nd.freq} kez)"))

            print()

    else:
        # ── Tüm Sonuçları Göster ──────────────────────────────────────────
        print_results(results, filepath)


if __name__ == "__main__":
    main()
