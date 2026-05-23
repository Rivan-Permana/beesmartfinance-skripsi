-- File: database/schemas/01_init_schema.sql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- A. MASTER DATA
CREATE TABLE ms_golongan (
    id SERIAL PRIMARY KEY,
    kode_golongan VARCHAR(5) UNIQUE NOT NULL,
    nama_golongan VARCHAR(50) NOT NULL,
    deskripsi TEXT
);

CREATE TABLE ms_sub_golongan (
    id SERIAL PRIMARY KEY,
    golongan_id INT REFERENCES ms_golongan(id) ON DELETE CASCADE,
    kode_sub VARCHAR(10) UNIQUE NOT NULL,
    nama_sub VARCHAR(100) NOT NULL
);

CREATE TABLE ms_coa (
    kode_akun VARCHAR(20) PRIMARY KEY,
    sub_golongan_id INT REFERENCES ms_sub_golongan(id),
    nama_akun VARCHAR(255) NOT NULL,
    posisi_normal CHAR(1) CHECK (posisi_normal IN ('D', 'K')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- B. OPERASIONAL
CREATE TABLE ms_siswa (
    id SERIAL PRIMARY KEY,
    nis VARCHAR(20) UNIQUE,
    nama_siswa VARCHAR(100) NOT NULL,
    kelas VARCHAR(20),
    status_katering BOOLEAN DEFAULT FALSE,
    status_jemputan BOOLEAN DEFAULT FALSE,
    alamat TEXT,
    nama_wali VARCHAR(100),
    no_telp_wali VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ms_pegawai (
    id SERIAL PRIMARY KEY,
    nip VARCHAR(20) UNIQUE,
    nama_pegawai VARCHAR(100) NOT NULL,
    jabatan VARCHAR(50),
    gaji_pokok NUMERIC(15,2) DEFAULT 0,
    tunjangan_jabatan NUMERIC(15,2) DEFAULT 0,
    tunjangan_transport NUMERIC(15,2) DEFAULT 0,
    status_aktif BOOLEAN DEFAULT TRUE
);

-- C. TRANSAKSI
CREATE TABLE tr_jurnal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    no_bukti VARCHAR(50) UNIQUE NOT NULL,
    tanggal DATE NOT NULL,
    keterangan TEXT,
    tipe_sumber VARCHAR(20) DEFAULT 'MANUAL',
    created_by INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tr_jurnal_detail (
    id BIGSERIAL PRIMARY KEY,
    jurnal_id UUID REFERENCES tr_jurnal(id) ON DELETE CASCADE,
    kode_akun VARCHAR(20) REFERENCES ms_coa(kode_akun),
    debit NUMERIC(15,2) DEFAULT 0 CHECK (debit >= 0),
    kredit NUMERIC(15,2) DEFAULT 0 CHECK (kredit >= 0),
    CONSTRAINT one_side_only CHECK (
        (debit > 0 AND kredit = 0) OR
        (kredit > 0 AND debit = 0) OR
        (debit = 0 AND kredit = 0)
    )
);

CREATE TABLE tr_anggaran (
    id SERIAL PRIMARY KEY,
    kode_akun VARCHAR(20) REFERENCES ms_coa(kode_akun),
    tahun_anggaran INT NOT NULL,
    bulan INT,
    nominal_anggaran NUMERIC(15,2) DEFAULT 0,
    keterangan TEXT
);

-- D. VIEWS
CREATE OR REPLACE VIEW v_neraca_saldo AS
SELECT
    mc.kode_akun, mc.nama_akun, mc.posisi_normal,
    COALESCE(SUM(tjd.debit), 0) as total_debit,
    COALESCE(SUM(tjd.kredit), 0) as total_kredit,
    CASE
        WHEN mc.posisi_normal = 'D' THEN COALESCE(SUM(tjd.debit - tjd.kredit), 0)
        ELSE COALESCE(SUM(tjd.kredit - tjd.debit), 0)
    END as saldo_akhir
FROM ms_coa mc
LEFT JOIN tr_jurnal_detail tjd ON mc.kode_akun = tjd.kode_akun
GROUP BY mc.kode_akun, mc.nama_akun, mc.posisi_normal;

CREATE OR REPLACE VIEW v_dataset_prediksi_kas AS
SELECT
    TO_CHAR(tj.tanggal, 'YYYY-MM') as periode,
    EXTRACT(YEAR FROM tj.tanggal) as tahun,
    EXTRACT(MONTH FROM tj.tanggal) as bulan,
    SUM(tjd.debit) as arus_kas_masuk,
    SUM(tjd.kredit) as arus_kas_keluar,
    SUM(tjd.debit - tjd.kredit) as net_cash_flow_bulanan
FROM tr_jurnal tj
JOIN tr_jurnal_detail tjd ON tj.id = tjd.jurnal_id
WHERE tjd.kode_akun LIKE '1.1.0%' OR tjd.kode_akun LIKE '1.2.0%'
GROUP BY 1, 2, 3
ORDER BY 1 ASC;
