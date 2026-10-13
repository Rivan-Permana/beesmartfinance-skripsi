import type { Coa } from "@/types/api"

function activeCoa(coa: Coa[]): Coa[] {
  return coa.filter((c) => c.is_active !== false)
}

/** Akun beban operasional (51xx–57xx) untuk kegiatan & jurnal beban. */
export function filterCoaBeban(coa: Coa[]): Coa[] {
  return activeCoa(coa).filter(
    (c) => /^5\d{3,}/.test(c.kode_akun) && !/^9/.test(c.kode_akun),
  )
}

/** Akun aset tetap (12x) untuk pencatatan aset. */
export function filterCoaAsetTetap(coa: Coa[]): Coa[] {
  return activeCoa(coa).filter((c) => /^12/.test(c.kode_akun))
}

/** Akun beban penyusutan / kepegawaian (53xx) untuk depresiasi aset. */
export function filterCoaBebanPenyusutan(coa: Coa[]): Coa[] {
  return activeCoa(coa).filter((c) => /^53/.test(c.kode_akun))
}

/** Akun pendapatan (41x) untuk tagihan manual. */
export function filterCoaPendapatan(coa: Coa[]): Coa[] {
  return activeCoa(coa).filter((c) => /^41/.test(c.kode_akun))
}
