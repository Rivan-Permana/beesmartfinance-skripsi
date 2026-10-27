import { describe, expect, it } from "vitest"

import { navForRoles, navItemActive, roleHome } from "./navigation"

describe("roleHome", () => {
  it("returns dashboard for Finance", () => {
    expect(roleHome(["Finance"])).toBe("/dashboard")
  })

  it("returns dashboard for SchoolPrincipal", () => {
    expect(roleHome(["SchoolPrincipal"])).toBe("/dashboard")
  })

  it("returns siswa for Administration", () => {
    expect(roleHome(["Administration"])).toBe("/siswa")
  })

  it("returns kegiatan for TeacherInCharge", () => {
    expect(roleHome(["TeacherInCharge"])).toBe("/kegiatan")
  })

  it("returns login when no role", () => {
    expect(roleHome([])).toBe("/login")
  })
})

describe("navForRoles", () => {
  it("filters nav items by role", () => {
    const adminNav = navForRoles(["Administration"])
    const paths = adminNav.map((n) => n.to)
    expect(paths).toContain("/siswa")
    expect(paths).toContain("/tagihan")
    expect(paths).not.toContain("/dashboard")
  })

  it("includes finance routes for Finance role", () => {
    const financeNav = navForRoles(["Finance"])
    const paths = financeNav.map((n) => n.to)
    expect(paths).toContain("/dashboard")
    expect(paths).toContain("/jurnal")
    expect(paths).toContain("/gaji")
    expect(paths).not.toContain("/absensi-siswa")
    expect(paths).not.toContain("/pegawai")
  })

  it("kepsek melihat menu pegawai dan anggaran kegiatan sesuai revisi", () => {
    const items = navForRoles(["SchoolPrincipal"])
    const paths = items.map((n) => n.to)
    expect(paths).toEqual(expect.arrayContaining(["/dashboard", "/kegiatan", "/pegawai", "/absensi-pegawai", "/gaji", "/pinjaman"]))
    expect(items.find((n) => n.to === "/kegiatan")?.label).toBe("Anggaran Kegiatan")
    expect(paths).not.toContain("/anggaran")
    expect(paths).not.toContain("/aset")
  })

  it("menambah menu sesuai revisi untuk Keuangan, Guru, dan Staf TU", () => {
    const finance = navForRoles(["Finance"]).map((n) => n.to + (n.query?.jenis ?? ""))
    expect(finance).toEqual(expect.arrayContaining(["/siswa", "/pendaftaran", "/jurnal", "/jurnalmasuk", "/gaji", "/pinjaman"]))
    expect(navForRoles(["TeacherInCharge"]).map((n) => n.to)).toEqual(expect.arrayContaining(["/absensi-siswa", "/rekap-siswa", "/kegiatan"]))
    const admin = navForRoles(["Administration"]).map((n) => n.to + (n.query?.jenis ?? ""))
    expect(admin).toEqual(expect.arrayContaining(["/jurnalmasuk", "/jurnalkeluar", "/absensi-siswa"]))
    expect(admin).not.toContain("/jurnal")
  })

  it("menandai Anggaran Kegiatan aktif di halaman anggaran per akun", () => {
    const item = navForRoles(["Finance"]).find((n) => n.label === "Anggaran Kegiatan")!
    expect(navItemActive(item, "/anggaran", undefined)).toBe(true)
    expect(navItemActive(item, "/kegiatan", undefined)).toBe(true)
    const jurnal = navForRoles(["Finance"]).find((n) => n.label === "Jurnal")!
    expect(navItemActive(jurnal, "/jurnal", "masuk")).toBe(false)
    expect(navItemActive(jurnal, "/jurnal", undefined)).toBe(true)
  })

  it("includes pegawai routes for Administration", () => {
    const adminNav = navForRoles(["Administration"])
    const paths = adminNav.map((n) => n.to)
    expect(paths).toContain("/pegawai")
    expect(paths).toContain("/absensi-pegawai")
  })
})
