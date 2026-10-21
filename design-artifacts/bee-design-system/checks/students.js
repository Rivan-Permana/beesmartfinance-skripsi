async (page) => {
  const paged = (results) => ({ count: results.length, next: null, previous: null, results })
  const groups = [{ id: 1, nama: 'Melati', jenjang: 1, jenjang_kode: 'TK A' }]
  let students = [{ id: 1, nis: 'CONTOH-001', nama: 'Siswa Contoh', status: 'aktif', kelompok: 1, spp_nominal: '750000.25', nama_ayah: 'Orang Tua Contoh', kontak_ayah: '0811111111', nama_ibu: '', kontak_ibu: '', alamat: '', tanggal_lahir: '2020-01-01', periode: 1 }]
  let failGroups = false
  let failStudents = false
  let rejectSave = true
  const interceptedWrites = []
  await page.unroute('**/api/**')
  await page.evaluate(() => localStorage.setItem('bee_access', 'synthetic-local-review'))
  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const path = new URL(request.url()).pathname.replace(/^.*\/api\/v1/, '')
    if (request.method() !== 'GET') {
      interceptedWrites.push({ path, method: request.method(), payload: request.postDataJSON() })
      if (request.method() === 'PUT' && path === '/siswa/1/') {
        if (rejectSave) return route.fulfill({ status: 400, json: { nis: ['NIS sudah digunakan.'] } })
        students = [{ ...students[0], ...request.postDataJSON() }]
        return route.fulfill({ status: 200, json: students[0] })
      }
      return route.fulfill({ status: 405, json: { detail: 'Local review: other mutations disabled' } })
    }
    let data = paged([])
    if (path === '/auth/me/') data = { id: 1, username: 'contoh', nama: 'Pengguna Contoh', is_superuser: false, groups: ['Administration'] }
    else if (path === '/siswa/') {
      if (failStudents) return route.fulfill({ status: 503, json: { detail: 'Synthetic failure' } })
      data = paged(students)
    } else if (path === '/kelompok/') {
      if (failGroups) return route.fulfill({ status: 503, json: { detail: 'Synthetic failure' } })
      data = paged(groups)
    }
    return route.fulfill({ status: 200, json: data })
  })
  try {
    await page.setViewportSize({ width: 1440, height: 1000 })
    await page.goto('http://127.0.0.1:4173/siswa')
    await page.locator('.directory-name').getByText('Siswa Contoh', {exact:true}).first().waitFor()
    await page.locator('.directory-loading').waitFor({ state: 'hidden' })
    await page.locator('#siswa-group-filter').click()
    await page.getByRole('option', {name:'TK A · Melati',exact:true}).click()
    await page.getByRole('listbox').waitFor({state:'hidden'})
    await page.locator('#siswa-group-filter').locator('..').getByRole('button',{name:'Hapus pilihan'}).click()
    if(await page.locator('#siswa-group-filter').innerText()!=='Semua' || await page.getByRole('listbox').count()) throw new Error('Group filter did not clear cleanly')
    await page.evaluate(() => document.fonts.ready)
    await page.screenshot({ path: 'design-artifacts/bee-design-system/role-Administration-03.png', scale: 'css', animations: 'disabled' })
    await page.getByRole('button', {name:'Ubah Siswa Contoh', exact:true}).first().click()
    const dialog = page.getByRole('dialog', {name:'Ubah data siswa'})
    await dialog.waitFor()
    const group = dialog.locator('#siswa-kelompok')
    for (const key of ['Space','Enter']) {
      await group.locator('..').getByRole('button',{name:'Hapus pilihan'}).press(key)
      if(await group.innerText()!=='Belum dikelompokkan' || await page.getByRole('listbox').count()) throw new Error('Keyboard clear failed or opened dropdown')
      if(await group.evaluate(e=>e!==document.activeElement)) throw new Error('Clear lost keyboard focus')
      await group.click()
      await page.getByRole('option',{name:'TK A · Melati',exact:true}).click()
      await page.getByRole('listbox').waitFor({state:'hidden'})
    }
    await page.setViewportSize({width:650,height:886})
    await dialog.locator('.p-dialog-content').evaluate(e=>{e.scrollTop=0})
    await page.screenshot({path:'design-artifacts/bee-design-system/ui-siswa-dialog.png',scale:'css',animations:'disabled'})
    await dialog.locator('#siswa-address').evaluate(e=>e.scrollIntoView({block:'end'}))
    await page.screenshot({path:'design-artifacts/bee-design-system/ui-siswa-dialog-scroll.png',scale:'css',animations:'disabled'})
    await page.setViewportSize({width:1440,height:1000})
    await dialog.locator('#siswa-name').fill('Siswa Contoh Diperbarui')
    await dialog.getByRole('button', {name:'Simpan perubahan'}).click()
    await dialog.getByText(/NIS sudah digunakan/).waitFor()
    const retainedName = await dialog.locator('#siswa-name').inputValue()
    if (retainedName !== 'Siswa Contoh Diperbarui') throw new Error('Form lost input after failure')
    const firstPayload = interceptedWrites[0].payload
    if (firstPayload.spp_nominal !== '750000.25' || firstPayload.kelompok !== 1 || firstPayload.kontak_ayah !== '0811111111') throw new Error('Unedited fields changed')
    rejectSave = false
    await dialog.getByRole('button', {name:'Simpan perubahan'}).click()
    await dialog.waitFor({state:'hidden'})
    await page.getByRole('button', {name:'Ubah data Siswa Contoh Diperbarui', exact:true}).first().waitFor()
    await page.setViewportSize({width:320,height:800})
    await page.waitForFunction(()=>document.documentElement.scrollWidth <= innerWidth)
    await page.locator('.p-toast-message').waitFor({state:'hidden'})
    await page.evaluate(()=>scrollTo(0,0))
    await page.screenshot({path:'design-artifacts/bee-design-system/role-Administration-mobile-03.png',scale:'css',animations:'disabled'})
    const mobile = await page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth}))
    failGroups = true
    await page.reload()
    await page.getByText('Daftar kelompok belum berhasil dimuat. Data siswa tetap tersedia.',{exact:true}).waitFor()
    if (await page.locator('.directory-mobile li').count() !== 1) throw new Error('Group failure hid students')
    await page.getByRole('button', {name:'Ubah Siswa Contoh Diperbarui',exact:true}).last().click()
    const partialDialog=page.getByRole('dialog',{name:'Ubah data siswa'})
    await partialDialog.getByText(/Kelompok siswa saat ini tetap dipertahankan/).waitFor()
    await page.keyboard.press('Escape')
    await partialDialog.waitFor({state:'hidden'})
    failStudents = true
    await page.reload()
    await page.getByText('Data siswa belum berhasil dimuat. Periksa koneksi, lalu coba lagi.',{exact:true}).waitFor()
    await page.getByRole('button',{name:'Coba muat ulang',exact:true}).waitFor()
    if (await page.locator('.directory-empty').count()) throw new Error('Failure misrepresented as empty data')
    return { retainedName, firstPayload, mobile, clearControl:'mouse/Space/Enter, no unwanted dropdown, focus returned', partialGroupFailure:'students retained', studentFailure:'retry offered, no empty-state fiction', interceptedWrites, source:'All API requests intercepted; no school data changed' }
  } finally {
    await page.unroute('**/api/**')
    await page.goto('http://127.0.0.1:4173/design-system.html#layar-siswa')
    await page.evaluate(()=>localStorage.removeItem('bee_access'))
  }
}
