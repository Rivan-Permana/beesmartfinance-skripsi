// Run with Playwright MCP browser_run_code_unsafe(filename). Local fixtures only.
async (page) => {
  const origin = 'http://127.0.0.1:4173/dashboard-preview.html';
  const checks = [
    ['Finance', 'Ringkasan keuangan', ['Tren kehadiran siswa', 'jurnal menunggu keputusan', 'Penggunaan anggaran']],
    ['SchoolPrincipal', 'Ikhtisar sekolah', ['Tren kehadiran siswa', 'Lanjutkan pencatatan']],
    ['Administration', 'Data siswa', ['Kas dan bank', 'Lanjutkan pencatatan', 'Penggunaan anggaran']],
    ['TeacherInCharge', 'Kegiatan sekolah', ['Kas dan bank', 'Catat pembayaran', 'Lanjutkan pencatatan']],
  ];
  const results = [];
  await page.goto(origin);
  for (const [role, title, forbidden] of checks) {
    await page.locator('#preview-role').selectOption(role);
    await page.getByRole('heading', { name: title, exact: true }).waitFor();
    const main = await page.locator('main').innerText();
    for (const text of forbidden) {
      if (main.includes(text)) throw new Error(`${role}: unexpected content ${text}`);
    }
    const links = await page.locator('main a[href^="?"]').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
    if (links.some(link => new URLSearchParams(link.slice(1)).get('role') !== role)) {
      throw new Error(`${role}: link overwrites role`);
    }
    if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) {
      throw new Error(`${role}: page overflows viewport`);
    }
    results.push(`${role}: content, role switch, links and viewport OK`);
  }
  const boundaries = [
    ['Finance', '/rekap-siswa', 'Ringkasan keuangan'],
    ['Finance', '/kegiatan', 'Ringkasan keuangan'],
    ['SchoolPrincipal', '/siswa', 'Ikhtisar sekolah'],
    ['Administration', '/dashboard', 'Data siswa'],
    ['TeacherInCharge', '/jurnal', 'Kegiatan sekolah'],
    ['TeacherInCharge', '/tagihan', 'Kegiatan sekolah'],
  ];
  for (const [role, screen, fallback] of boundaries) {
    await page.goto(`${origin}?${new URLSearchParams({ role, screen })}`);
    await page.getByRole('heading', { name: fallback, exact: true }).waitFor();
    results.push(`${role}: ${screen} falls back to own home`);
  }
  return results;
}
