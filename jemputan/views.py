# jemputan/views.py
from collections import defaultdict
import datetime
import calendar
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now

from .models import Jemputan
from .forms import KendaraanForm, RekapJemputanFilterForm, RekapJemputanBulananForm

from siswa.models import Siswa, SiswaJemputan, Kehadiran


# =======================
# Sub Menu 1: Data Kendaraan
# =======================

def kendaraan_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = Jemputan.objects.all().order_by("nama_supir", "no_kendaraan")
    if q:
        qs = qs.filter(
            Q(nama_supir__icontains=q)
            | Q(no_kendaraan__icontains=q)
            | Q(jenis_mobil__icontains=q)
        )
    return render(
        request,
        "jemputan/kendaraan_list.html",
        {"items": qs, "q": q, "title": "Data Kendaraan"},
    )


def kendaraan_create(request):
    if request.method == "POST":
        form = KendaraanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Kendaraan berhasil ditambahkan.")
            return redirect("kendaraan_list")
    else:
        form = KendaraanForm()
    return render(
        request,
        "jemputan/kendaraan_form.html",
        {"form": form, "title": "Tambah Kendaraan"},
    )


def kendaraan_update(request, pk):
    obj = get_object_or_404(Jemputan, pk=pk)
    if request.method == "POST":
        form = KendaraanForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Kendaraan berhasil diperbarui.")
            return redirect("kendaraan_list")
    else:
        form = KendaraanForm(instance=obj)
    return render(
        request,
        "jemputan/kendaraan_form.html",
        {"form": form, "title": "Ubah Kendaraan"},
    )


def kendaraan_delete(request, pk):
    obj = get_object_or_404(Jemputan, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Kendaraan berhasil dihapus.")
        return redirect("kendaraan_list")
    return render(
        request,
        "jemputan/kendaraan_confirm_delete.html",
        {"obj": obj, "title": "Hapus Kendaraan"},
    )


# =======================
# Rekapitulasi Jemputan Siswa
# =======================

def _month_range(first_day: datetime.date):
    last_day_num = calendar.monthrange(first_day.year, first_day.month)[1]
    return first_day, first_day.replace(day=last_day_num)

def rekap_jemputan(request):
    # form: tanggal_awal/akhir tetap dipakai; ada input <input type="month"> di template
    form = RekapJemputanFilterForm(request.GET or None)
    valid = form.is_valid()
    cd = form.cleaned_data if valid else {}
    t1 = cd.get("tanggal_awal") or now().date().replace(day=1)
    t2 = cd.get("tanggal_akhir") or now().date()
    q  = (cd.get("q") or "").strip()

    # Normalisasi agar range tetap 1 bulan penuh jika user pilih via month
    first_day = t1.replace(day=1)
    last_day  = t2.replace(day=calendar.monthrange(t2.year, t2.month)[1])
    days = [first_day + datetime.timedelta(days=i) for i in range((last_day - first_day).days + 1)]

    # siswa aktif + search nama
    siswa_qs = Siswa.objects.filter(status="aktif").select_related("kelompok__jenjang")
    if q:
        siswa_qs = siswa_qs.filter(nama__icontains=q)

    # ambil kehadiran di rentang (per hari)
    hadir_qs = Kehadiran.objects.filter(tanggal__range=[first_day, last_day]).select_related(
        "siswa", "siswa__kelompok", "siswa__kelompok__jenjang"
    )
    if q:
        hadir_qs = hadir_qs.filter(siswa__nama__icontains=q)

    # index: siswa_id -> { tanggal: entri }
    entri_map = defaultdict(dict)
    for e in hadir_qs:
        entri_map[e.siswa_id][e.tanggal] = e

    # bangun rows harian
    rows = []
    total_ikut_all = 0

    for s in siswa_qs.order_by("kelompok__jenjang__kode", "kelompok__nama", "nama"):
        harian_marks = []
        ikut_count = 0

        # untuk tiap tanggal
        for d in days:
            e = entri_map.get(s.id, {}).get(d)
            if e is None:
                harian_marks.append("")          # belum ada entri
            else:
                if e.jemput_datang or e.jemput_pulang:
                    harian_marks.append("v")      # ikut (datang/pulang True)
                    ikut_count += 1
                else:
                    harian_marks.append("x")      # ada entri, tapi keduanya False

        total_ikut_all += ikut_count

        rows.append({
            "siswa": s,
            "nis": getattr(s, "nis", None) or "-",
            "jenjang": s.kelompok.jenjang.nama if s.kelompok and s.kelompok.jenjang else "-",
            "harian": harian_marks,   # sama panjang dengan days
            "total_ikut": ikut_count,
        })

    context = {
        "form": form,
        "rows": rows,
        "summary_total_ikut": total_ikut_all,
        "title": "Rekapitulasi Jemputan Siswa (Bulanan)",
        "days": days,                # ⬅️ kirim daftar tanggal ke template
        "q": q,
    }
    return render(request, "jemputan/rekap_jemputan.html", context)


def _month_bounds(year: int, month: int):
    first = datetime.date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = datetime.date(year, month, last_day)
    return first, last

def rekap_jemputan_bulanan(request):
    # default: bulan berjalan
    today = now().date()
    default_bulan = f"{today.year:04d}-{today.month:02d}"

    form = RekapJemputanBulananForm(request.GET or None, initial={"bulan": default_bulan})
    # baca parameter
    bulan = (request.GET.get("bulan") or default_bulan).strip()
    q = (request.GET.get("q") or "").strip()

    kelompok_selected = request.GET.get("kelompok")
    periode_selected = request.GET.get("periode")

    # hitung first/last day dari 'bulan' (YYYY-MM)
    try:
        y, m = bulan.split("-")
        year, month = int(y), int(m)
    except Exception:
        year, month = today.year, today.month

    first_day, last_day = _month_bounds(year, month)
    days = [first_day + datetime.timedelta(days=i) for i in range((last_day - first_day).days + 1)]

    # siswa aktif sesuai filter
    siswa_qs = Siswa.objects.select_related("kelompok__jenjang").filter(status="aktif")
    if q:
        siswa_qs = siswa_qs.filter(nama__icontains=q)
    if kelompok_selected:
        siswa_qs = siswa_qs.filter(kelompok_id=kelompok_selected)
    if periode_selected:
        siswa_qs = siswa_qs.filter(periode_id=periode_selected)

    siswa_qs = siswa_qs.order_by("kelompok__jenjang__kode", "kelompok__nama", "nama")

    # ambil kehadiran rentang bulan, filter sama seperti siswa_qs
    hadir_qs = Kehadiran.objects.filter(tanggal__range=[first_day, last_day]).select_related(
        "siswa", "siswa__kelompok", "siswa__kelompok__jenjang"
    )
    if q:
        hadir_qs = hadir_qs.filter(siswa__nama__icontains=q)
    if kelompok_selected:
        hadir_qs = hadir_qs.filter(siswa__kelompok_id=kelompok_selected)
    if periode_selected:
        hadir_qs = hadir_qs.filter(siswa__periode_id=periode_selected)

    # index: siswa_id -> { tanggal: entri Kehadiran }
    entri_map = defaultdict(dict)
    for e in hadir_qs:
        entri_map[e.siswa_id][e.tanggal] = e

    # bangun struktur grup: jenjang -> [kelompok blocks]
    data = []
    total_ikut_all = 0

    # grouping manual
    def jenjang_key(s):  # (kode, nama)
        j = s.kelompok.jenjang if (s.kelompok and s.kelompok.jenjang) else None
        return (getattr(j, "kode", "-"), getattr(j, "nama", "-"))

    def kelompok_key(s):  # nama kelompok
        return getattr(s.kelompok, "nama", "-")

    # kumpulkan per jenjang -> kelompok -> siswa list
    grouped = defaultdict(lambda: defaultdict(list))
    for s in siswa_qs:
        grouped[jenjang_key(s)][kelompok_key(s)].append(s)

    for (j_kode, j_nama), kel_map in grouped.items():
        jenjang_block = {
            "jenjang": {"kode": j_kode, "nama": j_nama},
            "kelompok": [],
        }
        for k_nama, siswa_list in kel_map.items():
            siswa_rows = []
            subtotal_ikut = 0

            for s in siswa_list:
                marks = []
                ikut_count = 0
                per_siswa_map = entri_map.get(s.id, {})

                for d in days:
                    e = per_siswa_map.get(d)
                    if e is None:
                        marks.append("")  # belum ada entri
                    else:
                        if e.jemput_datang or e.jemput_pulang:
                            marks.append("v")
                            ikut_count += 1
                        else:
                            marks.append("x")

                subtotal_ikut += ikut_count
                total_ikut_all += ikut_count

                siswa_rows.append({
                    "siswa": s,
                    "nis": getattr(s, "nis", None) or "-",
                    "harian": marks,
                    "total_ikut": ikut_count,
                })

            jenjang_block["kelompok"].append({
                "kelompok": {"nama": k_nama},
                "siswa_rows": siswa_rows,
                "subtotal": {
                    "ikut": subtotal_ikut,
                }
            })
        # sort kelompok by name
        jenjang_block["kelompok"].sort(key=lambda x: x["kelompok"]["nama"])
        data.append(jenjang_block)

    # sort jenjang by kode
    data.sort(key=lambda x: x["jenjang"]["kode"])

    context = {
        "form": form,
        "title": "Rekap Jemputan Bulanan",
        "bulan": bulan,
        "first_day": first_day,
        "last_day": last_day,
        "days": days,
        "data": data,
        "summary_total_ikut": total_ikut_all,
        "q": q,
    }
    return render(request, "jemputan/rekap_jemputan_bulanan.html", context)