# keuangan/views.py
import calendar
import datetime
from collections import defaultdict
from django.shortcuts import render
from siswa.models import Jenjang, Kelompok, Siswa, Kehadiran
from .forms import KateringFilterForm

HARGA_SENIN_KAMIS = 20000
HARGA_JUMAT = 10000

def _month_range(first_day: datetime.date):
    last_day_num = calendar.monthrange(first_day.year, first_day.month)[1]
    return first_day, first_day.replace(day=last_day_num)

def daftar_siswa_katering(request):
    form = KateringFilterForm(request.GET or None)
    valid = form.is_valid()  # <-- WAJIB
    # meski invalid, cleaned_data tetap ada; tapi kita kasih default aman juga
    cleaned = getattr(form, "cleaned_data", {}) or {}
    bulan = cleaned.get("bulan") or datetime.date.today().replace(day=1)
    kelompok_selected = cleaned.get("kelompok")
    periode_selected  = cleaned.get("periode")

    first_day, last_day = _month_range(bulan)
    days = [first_day + datetime.timedelta(days=i) for i in range((last_day - first_day).days + 1)]

    # filter siswa
    siswa_qs = Siswa.objects.filter(status="aktif")
    if kelompok_selected:
        siswa_qs = siswa_qs.filter(kelompok=kelompok_selected)
    if periode_selected:
        siswa_qs = siswa_qs.filter(periode=periode_selected)

    # ambil kehadiran dalam sebulan
    hadir_qs = Kehadiran.objects.filter(tanggal__range=[first_day, last_day])
    if kelompok_selected:
        hadir_qs = hadir_qs.filter(siswa__kelompok=kelompok_selected)
    if periode_selected:
        hadir_qs = hadir_qs.filter(siswa__periode=periode_selected)

    entri_map = defaultdict(dict)  # siswa_id -> {tanggal: Kehadiran}
    for e in hadir_qs.select_related("siswa", "siswa__kelompok", "siswa__kelompok__jenjang"):
        entri_map[e.siswa_id][e.tanggal] = e

    # jenjang -> kelompok
    jenjang_list = list(Jenjang.objects.all().order_by("kode"))
    kelompok_by_jenjang = defaultdict(list)
    all_kelompok = Kelompok.objects.select_related("jenjang").order_by("jenjang__kode", "nama")
    if kelompok_selected:
        all_kelompok = all_kelompok.filter(pk=kelompok_selected.pk)
    for k in all_kelompok:
        kelompok_by_jenjang[k.jenjang_id].append(k)

    data = []
    any_data = False

    for j in jenjang_list:
        kels = kelompok_by_jenjang.get(j.id, [])
        if not kels: continue
        jblock = {"jenjang": j, "kelompok": []}

        for k in kels:
            siswas = list(siswa_qs.filter(kelompok=k).order_by("nama"))
            rows = []
            sub_ikut = sub_monkam = sub_jumat = sub_harga = 0

            for s in siswas:
                harian = []
                ikut_cnt = monkam_cnt = jumat_cnt = 0

                for d in days:
                    e = entri_map.get(s.id, {}).get(d)
                    if not e or not e.katering:
                        harian.append("")
                        continue
                    v = (e.katering or "").lower()
                    if v == "ikut":
                        harian.append("I")
                        if d.weekday() == 4:
                            jumat_cnt += 1
                        elif d.weekday() in (0,1,2,3):
                            monkam_cnt += 1
                        ikut_cnt += 1
                    elif v == "tidak_ikut":
                        harian.append("T")
                    else:
                        harian.append("")

                harga = monkam_cnt * HARGA_SENIN_KAMIS + jumat_cnt * HARGA_JUMAT
                sub_ikut += ikut_cnt
                sub_monkam += monkam_cnt
                sub_jumat += jumat_cnt
                sub_harga += harga
                if ikut_cnt or monkam_cnt or jumat_cnt:
                    any_data = True

                rows.append({
                    "siswa": s,
                    "harian": harian,
                    "ikut_total": ikut_cnt,
                    "monkam_total": monkam_cnt,
                    "jumat_total": jumat_cnt,
                    "harga_total": harga,
                })

            jblock["kelompok"].append({
                "kelompok": k,
                "siswa_rows": rows,
                "subtotal": {
                    "ikut": sub_ikut,
                    "mon_kam": sub_monkam,
                    "jumat": sub_jumat,
                    "harga": sub_harga,
                }
            })

        if jblock["kelompok"]:
            data.append(jblock)

    fallback_siswa = []
    if not any_data:
        fallback_siswa = list(
            siswa_qs.select_related("kelompok", "kelompok__jenjang")
                    .order_by("kelompok__jenjang__kode", "kelompok__nama", "nama")
        )

    return render(request, "katering/daftar_siswa_katering.html", {
        "form": form,
        "data": data,
        "fallback_siswa": fallback_siswa,
        "title": "Lihat Siswa Katering (Bulanan)",
        "bulan": bulan,
        "first_day": first_day,
        "last_day": last_day,
        "days": days,
        "HARGA_SENIN_KAMIS": HARGA_SENIN_KAMIS,
        "HARGA_JUMAT": HARGA_JUMAT,
    })
