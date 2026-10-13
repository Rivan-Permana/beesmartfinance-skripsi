import { describe, expect, it } from "vitest"

import { navForRoles, roleHome } from "./navigation"

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

  it("kepsek tidak melihat menu pegawai operasional", () => {
    const paths = navForRoles(["SchoolPrincipal"]).map((n) => n.to)
    expect(paths).toContain("/dashboard")
    expect(paths).toContain("/kegiatan")
    expect(paths).not.toContain("/pegawai")
    expect(paths).not.toContain("/gaji")
    expect(paths).not.toContain("/pinjaman")
    expect(paths).not.toContain("/aset")
  })

  it("includes pegawai routes for Administration", () => {
    const adminNav = navForRoles(["Administration"])
    const paths = adminNav.map((n) => n.to)
    expect(paths).toContain("/pegawai")
    expect(paths).toContain("/absensi-pegawai")
  })
})
