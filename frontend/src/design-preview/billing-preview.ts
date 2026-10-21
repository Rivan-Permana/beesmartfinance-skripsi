import type { Role } from "@/types/api"
import { bills, students } from "./fixtures"

export interface BillComponent { id: string; label: string; total: number; paid: number | null }
export interface Allocation { component: string; amount: number }
export interface DemoPayment { proof: string; date: string; account: string; amount: number; allocations: Allocation[]; journal: string }
export interface DemoBill { id: string; student: string; studentId: string; group: string; period: string; components: BillComponent[]; payments: DemoPayment[] }
export const paymentAccounts = [{ code: "1.1.01", name: "Kas di Tangan" }, { code: "1.1.02", name: "Kas di Bank" }]
export function billTotals(bill: DemoBill) {
  const total = bill.components.reduce((sum, line) => sum + line.total, 0)
  const paid = bill.components.some((line) => line.paid === null) ? null : bill.components.reduce((sum, line) => sum + line.paid!, 0)
  return { total, paid, remaining: paid === null ? null : total - paid }
}
export function billStatus(bill: DemoBill) {
  const { paid, remaining } = billTotals(bill)
  if (remaining === null) return { value: "matching", label: "Perlu dicocokkan", tone: "warning" }
  if (remaining === 0) return { value: "paid", label: "Lunas", tone: "success" }
  return paid === 0 ? { value: "unpaid", label: "Belum bayar", tone: "warning" } : { value: "partial", label: "Sebagian dibayar", tone: "brand" }
}
export function canPayBill(bill: DemoBill, role: Role) {
  const totals = billTotals(bill)
  return role === "Administration" && totals.remaining !== null && Number.isSafeInteger(totals.remaining) && totals.remaining > 0
    && bill.components.every((line) => Number.isSafeInteger(line.total) && line.total >= 0 && line.paid !== null && Number.isSafeInteger(line.paid) && line.paid >= 0 && line.paid <= line.total)
}
export function validAllocation(bill: DemoBill, allocations: Allocation[]) {
  const ids = allocations.map((allocation) => allocation.component)
  const amount = allocations.reduce((sum, allocation) => sum + Number(allocation.amount), 0)
  // shortcut: whole-rupiah examples; retain the API decimal/idempotency contract on integration.
  return canPayBill(bill, "Administration") && ids.length > 0 && new Set(ids).size === ids.length
    && Number.isSafeInteger(amount) && amount > 0
    && allocations.every((allocation) => {
      const line = bill.components.find((component) => component.id === allocation.component)
      return line && line.paid !== null && Number.isSafeInteger(Number(allocation.amount)) && Number(allocation.amount) >= 0 && Number(allocation.amount) <= line.total - line.paid
    })
}
export function createDemoBills(): DemoBill[] {
  return bills.map((bill, index) => {
    const spp = students[index]!.spp
    return {
      id: `TAG-CONTOH-00${index + 1}`, student: bill.name, studentId: students[index]!.id, group: bill.group, period: "Oktober 2026",
      components: [
        { id: "spp", label: "SPP", total: spp, paid: bill.paid },
        { id: "katering", label: "Katering", total: bill.total - spp, paid: bill.paid === null ? null : 0 },
      ],
      payments: index === 1 ? [{ proof: "CONTOH-PBY-001", date: "2026-10-10", account: "1.1.02", amount: 600_000, allocations: [{ component: "spp", amount: 600_000 }], journal: "CONTOH-JRN-PBY-001" }] : [],
    }
  })
}
const demo = createDemoBills()
console.assert(demo.every((bill, index) => billTotals(bill).total === bills[index]!.total && billTotals(bill).paid === bills[index]!.paid && billTotals(bill).remaining === bills[index]!.remaining)
  && canPayBill(demo[0]!, "Administration") && !canPayBill(demo[0]!, "Finance") && !canPayBill(demo[0]!, "SchoolPrincipal")
  && !canPayBill(demo[2]!, "Administration") && billTotals(demo[2]!).remaining === null
  && validAllocation(demo[1]!, [{ component: "spp", amount: 150_000 }, { component: "katering", amount: 200_000 }])
  && !validAllocation(demo[1]!, [{ component: "spp", amount: 150_001 }])
  && !validAllocation(demo[1]!, [{ component: "spp", amount: 1 }, { component: "spp", amount: 1 }])
  && !validAllocation(demo[0]!, [{ component: "unknown", amount: 1 }]), "Billing preview totals or action boundaries do not match")
