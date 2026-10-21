// Historical 0.10 action-column review; superseded by checks/payroll.js for 0.11.
async (page) => {
  const paged = results => ({count:results.length,next:null,previous:null,results})
  const staff = ['Pegawai Contoh A','Pegawai Contoh B','Pegawai Contoh C'].map((nama,i)=>({id:i+1,nama,status_aktif:true,nip:null,jabatan:'Guru contoh'}))
  const salary = staff.map((p,i)=>({id:i+1,pegawai:p.id,periode_bulan:10,periode_tahun:2026,gaji_pokok:'4000000',tunjangan_jabatan:'100000',tunjangan_pengabdian:'0',tunjangan_asuransi:'0',uang_makan:'0',transport:'0',bonus_insentif:'0',thr:'0',hari_hadir:0,potongan_pinjaman:'100000',potongan_asuransi:'0',total_bruto:'4100000',total_potongan:'100000',total_netto:'4000000',jurnal:i===0?'CONTOH-JURNAL':null}))
  const loans = staff.map((p,i)=>({id:i+1,pegawai:p.id,tanggal_pinjaman:'2026-10-01',jumlah_pinjaman:'1000000',tenor_bulan:2,angsuran_per_bulan:'500000',sudah_terbayar:'0',sisa_pinjaman:'1000000',jurnal:i===0?'CONTOH-JURNAL':null}))
  const geometry = [], errors = [], mutations = []
  const onError = e => errors.push(String(e))
  page.on('pageerror',onError)
  await page.unroute('**/api/**')
  await page.evaluate(()=>localStorage.setItem('bee_access','synthetic-local-review'))
  await page.route('**/api/**',async route=>{
    const request = route.request(), path = new URL(request.url()).pathname.replace(/^.*\/api\/v1/,'')
    if(request.method()!=='GET') {
      mutations.push({path,method:request.method()})
      return route.fulfill({status:405,json:{detail:'Local UI review: mutations blocked'}})
    }
    let data = paged([])
    if(path==='/auth/me/') data={id:1,username:'contoh',groups:['Finance'],is_superuser:false}
    else if(path==='/pegawai/')data=paged(staff)
    else if(path==='/gaji/')data=paged(salary)
    else if(path==='/pinjaman/')data=paged(loans)
    else if(path==='/gaji/2/')data=salary[1]
    return route.fulfill({json:data})
  })
  const row = name => page.locator('.employee-finance-table tbody tr').filter({hasText:name})
  async function reviewWidths(screen) {
    for(const width of [1440,1024,768,390,320]) {
      await page.setViewportSize({width,height:900})
      const result = await page.locator('.employee-finance-table').evaluate(el=>{
        const groups=[...el.querySelectorAll('.employee-row-actions')]
        const cells=[...el.querySelectorAll('tbody tr')].map(e=>e.getBoundingClientRect().height)
        const oneLine=groups.every(e=>{const b=[...e.querySelectorAll('button')].map(e=>e.getBoundingClientRect());return b.every(r=>Math.abs(r.y-b[0].y)<1)&&e.scrollWidth<=e.clientWidth+1})
        const primary=groups.map(e=>e.querySelector('button').getBoundingClientRect().right)
        return {width:innerWidth,pageWidth:document.documentElement.scrollWidth,oneLine,consistentHeight:Math.max(...cells)-Math.min(...cells)<1,primaryAligned:Math.max(...primary)-Math.min(...primary)<1}
      })
      if(result.pageWidth>width||!result.oneLine||!result.consistentHeight||!result.primaryAligned)throw new Error(`${screen}: ${JSON.stringify(result)}`)
      geometry.push({screen,...result})
    }
    await page.setViewportSize({width:1440,height:900})
    await page.evaluate(()=>document.fonts.ready)
    await page.screenshot({path:`design-artifacts/bee-design-system/employee-actions-${screen}.png`,scale:'css',animations:'disabled'})
  }
  try {
    await page.goto('http://127.0.0.1:4173/gaji')
    await row('Pegawai Contoh B').waitFor()
    await page.getByRole('button',{name:'Tindakan slip Pegawai Contoh B',exact:true}).waitFor()
    if(await row('Pegawai Contoh A').getByRole('button',{name:/Tindakan slip/}).count())throw new Error('Posted payroll exposes write actions')
    await reviewWidths('gaji')
    const trigger = page.getByRole('button',{name:'Tindakan slip Pegawai Contoh B',exact:true})
    await trigger.focus();await trigger.press('Enter')
    await page.getByRole('menuitem',{name:'Posting ke jurnal',exact:true}).waitFor()
    if(await page.getByRole('menuitem').count()!==3)throw new Error('Payroll menu actions missing')
    await page.screenshot({path:'design-artifacts/bee-design-system/employee-actions-gaji-menu.png',scale:'css',animations:'disabled'})
    await page.keyboard.press('Escape')
    await page.getByRole('menu').waitFor({state:'hidden'})
    if(await trigger.evaluate(e=>e!==document.activeElement))throw new Error('Payroll menu lost keyboard focus')
    await trigger.click();await page.getByRole('menuitem',{name:'Hapus slip',exact:true}).click()
    await page.getByRole('alertdialog').getByText('Hapus slip gaji ini? Hanya slip yang belum dijurnal.',{exact:true}).waitFor()
    await page.getByRole('alertdialog').getByRole('button',{name:'Batal',exact:true}).click()
    await page.getByRole('alertdialog').waitFor({state:'hidden'})
    await trigger.click();await page.getByRole('menuitem',{name:'Ubah slip',exact:true}).click()
    await page.getByRole('dialog',{name:'Edit Slip Gaji',exact:true}).waitFor()
    await page.getByRole('dialog').getByRole('button',{name:'Batal',exact:true}).click()
    await page.getByRole('dialog').waitFor({state:'hidden'})
    await page.getByRole('button',{name:'Lihat slip Pegawai Contoh B Oktober 2026',exact:true}).click()
    await page.getByRole('dialog',{name:'Slip Gaji',exact:true}).getByText('Pegawai Contoh B',{exact:true}).waitFor()
    await page.getByRole('dialog').locator('.p-dialog-footer').getByRole('button',{name:'Tutup',exact:true}).click()
    await page.getByRole('dialog').waitFor({state:'hidden'})
    await page.goto('http://127.0.0.1:4173/pinjaman')
    await row('Pegawai Contoh B').waitFor()
    if(await row('Pegawai Contoh A').getByRole('button').count())throw new Error('Disbursed loan exposes actions')
    await reviewWidths('kasbon')
    await page.getByRole('button',{name:'Tindakan kasbon Pegawai Contoh B',exact:true}).click()
    await page.getByRole('menuitem',{name:'Ubah kasbon',exact:true}).waitFor()
    if(await page.getByRole('menuitem').count()!==2)throw new Error('Loan menu actions missing')
    await page.screenshot({path:'design-artifacts/bee-design-system/employee-actions-kasbon-menu.png',scale:'css',animations:'disabled'})
    await page.getByRole('menuitem',{name:'Hapus pengajuan',exact:true}).click()
    await page.getByRole('alertdialog').getByText('Hapus pengajuan kasbon ini? Hanya yang belum dicairkan.',{exact:true}).waitFor()
    await page.getByRole('alertdialog').getByRole('button',{name:'Batal',exact:true}).click()
    await page.getByRole('alertdialog').waitFor({state:'hidden'})
    await page.getByRole('button',{name:'Tindakan kasbon Pegawai Contoh B',exact:true}).click()
    await page.getByRole('menuitem',{name:'Ubah kasbon',exact:true}).click()
    await page.getByRole('dialog',{name:'Edit Kasbon',exact:true}).waitFor()
    await page.getByRole('dialog').getByRole('button',{name:'Batal',exact:true}).click()
    await page.getByRole('dialog').waitFor({state:'hidden'})
    await page.getByRole('button',{name:'Cairkan kasbon Pegawai Contoh B',exact:true}).click()
    const confirm=page.getByRole('alertdialog')
    await confirm.getByText(/Cairkan kasbon Pegawai Contoh B/).waitFor()
    await confirm.getByRole('button',{name:'Batal',exact:true}).click()
    if(mutations.length||errors.length)throw new Error(JSON.stringify({mutations,errors}))
    return {ok:true,geometry,checks:['single-line actions','consistent row height','aligned primary action','posted/disbursed write guards','keyboard menu and Escape focus','edit opens correct record','view slip','delete confirmations preserved','disbursement confirmation preserved'],mutations,errors,scope:'Synthetic fixtures only; all API mutations blocked'}
  } finally {
    page.off('pageerror',onError)
    await page.unroute('**/api/**')
    await page.evaluate(()=>{localStorage.removeItem('bee_access');localStorage.removeItem('bee_refresh');document.querySelector('#app')?.__vue_app__?.unmount()})
    await page.setViewportSize({width:1440,height:1000})
    await page.goto('http://127.0.0.1:4173/login')
  }
}
