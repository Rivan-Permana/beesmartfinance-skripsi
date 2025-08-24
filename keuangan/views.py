from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from .models import COA
from .forms import COAForm
from .models import Keuangan
from .forms import KeuanganForm
import math
import re

# Helper: map slug kategori ke enum model

CATEGORY_SLUGS = {"tk": COA.Category.TK, "playgroup": COA.Category.PLAYGROUP}
def _category_from_slug(slug): return CATEGORY_SLUGS[slug.lower()]

def daftar_keuangan(request):
    keuangan_list = Keuangan.objects.all().order_by('-tanggal')
    return render(request, 'keuangan/daftar_keuangan.html', {'keuangan_list': keuangan_list})

def tambah_keuangan(request):
    form = KeuanganForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('daftar_keuangan')
    return render(request, 'keuangan/form_keuangan.html', {'form': form})

def edit_keuangan(request, pk):
    keuangan = get_object_or_404(Keuangan, pk=pk)
    form = KeuanganForm(request.POST or None, instance=keuangan)
    if form.is_valid():
        form.save()
        return redirect('daftar_keuangan')
    return render(request, 'keuangan/form_keuangan.html', {'form': form})

def hapus_keuangan(request, pk):
    keuangan = get_object_or_404(Keuangan, pk=pk)
    keuangan.delete()
    return redirect('daftar_keuangan')

# COA
def _category_from_slug(slug):
    key = (slug or "").lower()
    if key not in CATEGORY_SLUGS:
        raise ValueError("Kategori tidak dikenali")
    return CATEGORY_SLUGS[key]

# keuangan/views.py

def _parse_segments(s: str):
    """Kembalikan tuple segmen int untuk '4.1.01' -> (4,1,1).
       Jika ada segmen non-digit, segmen itu jadi besar supaya di bawah."""
    segs = []
    for part in s.split("."):
        if re.fullmatch(r"\d+", part or ""):
            segs.append(int(part))
        else:
            # segmen aneh -> taruh jauh di bawah
            segs.append(10**12)
    return tuple(segs)

def _coa_sort_key(obj):
    s = (obj.nomor_akun or "").strip()
    if not s:
        return (math.inf, 3, math.inf, ())  # kosong ke paling bawah

    # KODE BERTITIK (hierarkis seperti 4.1.01)
    if "." in s:
        segs = _parse_segments(s)
        group = segs[0] if segs else math.inf
        return (group, 2, segs[0], segs)  # grup -> level=2 -> urut per segmen

    # KODE NUMERIK MURNI (1, 11, 1101, ...)
    if s.isdigit():
        n = int(s)
        group = int(s[0])  # grup = digit pertama
        is_root = 0 if len(s) == 1 else 1  # akun akar (1 digit) dulu
        # dalam grup numerik, urutkan naik berdasarkan nilai int utuh
        return (group, is_root, n, (n,))
    
    # Kode non-angka selain dotted -> paling bawah
    return (math.inf, 3, math.inf, ())

def coa_list(request, slug):
    category = _category_from_slug(slug)
    q = request.GET.get("q", "").strip()

    qs = COA.objects.filter(category=category)
    if q:
        qs = qs.filter(
            Q(nomor_akun__icontains=q) |
            Q(tipe_akun__icontains=q) |
            Q(nama_akun__icontains=q)
        )

    items = sorted(qs, key=_coa_sort_key)

    return render(request, "keuangan/coa_list.html", {
        "items": items,
        "category": category,
        "slug": slug,
        "title": f"COA {category}",
        "q": q,
    })

def coa_create(request, slug):
    category = _category_from_slug(slug)

    if request.method == "POST":
        form = COAForm(request.POST)           # ⬅️ TANPA category=
        if form.is_valid():
            obj = form.save(commit=False)
            obj.category = category            # ⬅️ set kategori di sini
            obj.save()
            messages.success(request, "Akun berhasil ditambahkan.")
            return redirect(reverse("coa_list", args=[slug]))
    else:
        form = COAForm()                       # ⬅️ TANPA category=

    return render(request, "keuangan/coa_form.html", {
        "form": form, "category": category, "slug": slug,
        "title": f"Tambah COA {category}",
    })


def coa_update(request, slug, pk):
    category = _category_from_slug(slug)
    obj = get_object_or_404(COA, pk=pk, category=category)

    if request.method == "POST":
        form = COAForm(request.POST, instance=obj)   # ⬅️ TANPA category=
        if form.is_valid():
            form.save()
            messages.success(request, "Akun berhasil diperbarui.")
            return redirect(reverse("coa_list", args=[slug]))
    else:
        form = COAForm(instance=obj)                 # ⬅️ TANPA category=

    return render(request, "keuangan/coa_form.html", {
        "form": form, "category": category, "slug": slug,
        "title": f"Ubah COA {category}", "obj": obj,
    })


def coa_delete(request, slug, pk):
    category = _category_from_slug(slug)
    obj = get_object_or_404(COA, pk=pk, category=category)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Akun berhasil dihapus.")
        return redirect(reverse("coa_list", args=[slug]))
    return render(request, "keuangan/coa_confirm_delete.html", {
        "category": category, "slug": slug, "title": f"Hapus COA {category}", "obj": obj,
    })
