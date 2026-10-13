import { beforeEach, describe, expect, it } from "vitest"

import router from "./router"
import { useAuthStore } from "@/stores/auth"

describe("router guard", () => {
  beforeEach(async () => {
    const auth = useAuthStore()
    auth.$reset()
    auth.ready = true
    await router.push("/login")
  })

  it("redirects unauthenticated user to login", async () => {
    await router.push("/dashboard")
    expect(router.currentRoute.value.name).toBe("login")
    expect(router.currentRoute.value.query.next).toBe("/dashboard")
  })

  it("redirects Administration away from finance-only routes", async () => {
    const auth = useAuthStore()
    auth.user = {
      id: 1,
      username: "admin.tu",
      nama: "Bu Fitri",
      is_superuser: false,
      groups: ["Administration"],
    }
    await router.push("/dashboard")
    expect(router.currentRoute.value.path).toBe("/siswa")
  })

  it("allows Finance to access dashboard", async () => {
    const auth = useAuthStore()
    auth.user = {
      id: 2,
      username: "keuangan",
      nama: "Staff Keuangan",
      is_superuser: false,
      groups: ["Finance"],
    }
    await router.push("/dashboard")
    expect(router.currentRoute.value.name).toBe("dashboard")
  })

  it("allows Administration to access tagihan", async () => {
    const auth = useAuthStore()
    auth.user = {
      id: 1,
      username: "admin.tu",
      nama: "Bu Fitri",
      is_superuser: false,
      groups: ["Administration"],
    }
    await router.push("/tagihan")
    expect(router.currentRoute.value.name).toBe("tagihan")
  })

  it("allows Administration to access pegawai & absensi pegawai", async () => {
    const auth = useAuthStore()
    auth.user = {
      id: 1,
      username: "admin.tu",
      nama: "Bu Fitri",
      is_superuser: false,
      groups: ["Administration"],
    }
    await router.push("/pegawai")
    expect(router.currentRoute.value.name).toBe("pegawai")
    await router.push("/absensi-pegawai")
    expect(router.currentRoute.value.name).toBe("absensi-pegawai")
  })
})
