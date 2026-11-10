// Pengisian COA + kode pengeluaran produksi lewat sesi Keuangan (pola 2/11).
// Jalankan di tab produksi yang sudah login sebagai keuangan.
//   await coaKode({ apply: false })  -> kondisi awal + rencana + konflik (tanpa menulis)
//   await coaKode({ apply: true })   -> hanya bila dry-run bersih dan backup bernama sudah ada
async function coaKode({ apply = false } = {}) {
  const BASE = "/api/v1"
  const H = () => ({ Authorization: `Bearer ${localStorage.getItem("bee_access")}`, "Content-Type": "application/json" })
  const call = async (method, path, body) => {
    const r = await fetch(BASE + path, { method, headers: H(), body: body ? JSON.stringify(body) : undefined })
    const text = await r.text()
    return { status: r.status, data: text ? JSON.parse(text) : null }
  }
  const AKUN = [
    ["115", "11", "Kas PG", "D"], ["116", "11", "Kas TK", "D"], ["117", "11", "Kas ADM", "D"], ["118", "11", "Kas Rekening Sekolah", "D"],
    ["5134", "51", "TK-Beban Operasional-Kegiatan KBM", "D"], ["5135", "51", "TK-Beban Operasional-Fun Games", "D"],
    ["5136", "51", "TK-Beban Operasional-Motorik Kasar", "D"], ["5137", "51", "TK-Beban Operasional-Perlengkapan Kelas", "D"],
    ["5138", "51", "TK-Beban Operasional-MPLS", "D"],
    ["5234", "52", "PG-Beban Operasional-Kegiatan KBM", "D"], ["5235", "52", "PG-Beban Operasional-Fun Games", "D"],
    ["5236", "52", "PG-Beban Operasional-Motorik Kasar", "D"], ["5237", "52", "PG-Beban Operasional-Perlengkapan Kelas", "D"],
    ["5238", "52", "PG-Beban Operasional-MPLS", "D"],
    ["5409", "54", "Beban Pengadaan Seragam Siswa", "D"], ["5410", "54", "Beban Seragam IGRA", "D"],
    ["313", "31", "Pembagian Dana ke Yayasan", "K"],
  ]
  const KODE = [ // [kode, unit, akun, nama]
    ["KEG", "TK", "5134", "Kegiatan KBM"], ["KEG-COOK", "TK", "5116", "Fun Cooking"], ["KEG-FUN", "TK", "5135", "Fun Games"],
    ["KEG-MK", "TK", "5136", "Motorik Kasar"], ["KEG-BELADIRI", "TK", "5118", "Olah raga bela diri"],
    ["KLS", "TK", "5137", "Perlengkapan kelas"], ["MPBS", "TK", "5138", "MPLS anak"],
    ["KEG", "PG", "5234", "Kegiatan KBM"], ["KEG-COOK", "PG", "5216", "Fun Cooking"], ["KEG-FUN", "PG", "5235", "Fun Games"],
    ["KEG-MK", "PG", "5236", "Motorik Kasar"], ["KLS", "PG", "5237", "Perlengkapan kelas"], ["MPBS", "PG", "5238", "MPLS anak"],
    ["SRG", "UMUM", "5409", "Seragam siswa"], ["SRGI", "UMUM", "5410", "Seragam IGRA (dana BOP)"], ["DVD", "UMUM", "313", "Transfer ke yayasan"],
  ]
  const NONAKTIF_UMUM = ["KEG", "FUN", "KLS", "MK", "MPBS"]

  const coa = []
  for (let page = 1; ; page++) {
    const r = await call("GET", `/coa/?page_size=200&page=${page}`)
    if (r.status !== 200) return { error: `GET coa ${r.status}` }
    coa.push(...(r.data.results ?? r.data))
    if (!r.data.next) break
  }
  const kode = (await call("GET", "/kode-pengeluaran/")).data
  const adaAkun = new Map(coa.map(a => [a.kode_akun, a]))
  const kunci = (k, u) => `${k}|${u}`
  const adaKode = new Map(kode.map(k => [kunci(k.kode, k.unit), k]))
  const awal = {
    coa_total: coa.length,
    coa_kas: coa.filter(a => a.is_kas).map(a => `${a.kode_akun}:${a.nama_akun}`),
    kode: kode.map(k => `${k.id}:${k.kode}/${k.unit}/${k.akun ?? "-"}/${k.aktif ? "A" : "N"}`).join(" "),
  }
  const konflik = []
  const rencana = []
  for (const [k, sub, nama, pos] of AKUN) {
    const a = adaAkun.get(k)
    if (a && a.nama_akun !== nama) konflik.push(`akun ${k} sudah dipakai: ${a.nama_akun}`)
    else if (!a) rencana.push(["POST", "/coa/", { kode_akun: k, sub_golongan: sub, nama_akun: nama, posisi_normal: pos, is_active: true }])
  }
  for (const [k, unit, akun, nama] of KODE) {
    if (!adaAkun.has(akun) && !AKUN.some(x => x[0] === akun)) konflik.push(`akun ${akun} untuk ${k}/${unit} tidak ada`)
    const ada = adaKode.get(kunci(k, unit))
    if (!ada) rencana.push(["POST", "/kode-pengeluaran/", { kode: k, unit, nama, akun, aktif: true }])
    else if (ada.akun !== akun || !ada.aktif) {
      if (ada.akun && ada.akun !== akun) konflik.push(`${k}/${unit} sudah dipetakan ke ${ada.akun}`)
      else rencana.push(["PATCH", `/kode-pengeluaran/${ada.id}/`, { akun, nama: ada.nama || nama, aktif: true }])
    }
  }
  for (const k of NONAKTIF_UMUM) {
    const ada = adaKode.get(kunci(k, "UMUM"))
    if (ada && ada.aktif && !(KODE.some(x => x[0] === k && x[1] === "UMUM"))) rencana.push(["PATCH", `/kode-pengeluaran/${ada.id}/`, { aktif: false }])
  }
  if (!apply) return { awal, konflik, rencana: rencana.map(([m, p, b]) => `${m} ${p} ${JSON.stringify(b)}`) }
  if (konflik.length) return { error: "Ada konflik; tidak ada yang ditulis.", konflik }
  const hasil = []
  for (const [m, p, b] of rencana) {
    const r = await call(m, p, b)
    hasil.push(`${r.status} ${m} ${p} ${r.status >= 300 ? JSON.stringify(r.data) : ""}`)
    if (r.status >= 300) return { berhenti: true, hasil }
  }
  const akhir = (await call("GET", "/kode-pengeluaran/")).data
  return {
    hasil,
    kode_aktif: akhir.filter(k => k.aktif).length,
    aktif_belum_dipetakan: akhir.filter(k => k.aktif && !k.akun).map(k => `${k.kode}/${k.unit}`),
  }
}
