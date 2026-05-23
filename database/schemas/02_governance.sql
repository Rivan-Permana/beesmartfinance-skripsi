-- File: database/schemas/02_governance.sql
-- Schema v2: maker-checker, audit trail, soft-delete, periode fiskal,
-- kontrol anggaran, immutability jurnal POSTED, indexing.
-- Diterapkan SETELAH 01_init_schema.sql pada database yang sudah berisi data ETL.
-- Catatan: FK kolom user (created_by_id, dst) ditambahkan terpisah di 03_user_fk.sql
--          setelah app Django `accounts` (accounts_user) dibuat.

BEGIN;

-- =========================================================
-- 1. PERIODE AKUNTANSI (tahun ajaran / fiscal year)
-- =========================================================
CREATE TABLE IF NOT EXISTS ms_periode_akuntansi (
    id          SERIAL PRIMARY KEY,
    kode        VARCHAR(20) UNIQUE NOT NULL,          -- contoh: '2025/2026'
    tgl_mulai   DATE NOT NULL,
    tgl_selesai DATE NOT NULL,
    status      VARCHAR(10) NOT NULL DEFAULT 'OPEN'
                CHECK (status IN ('OPEN', 'CLOSED')),
    CONSTRAINT chk_periode_range CHECK (tgl_selesai > tgl_mulai)
);

-- =========================================================
-- 2. tr_jurnal: maker-checker + soft-delete + reversal + periode
--    (Konvensi nama kolom user disamakan dgn Django: <field>_id)
-- =========================================================
ALTER TABLE tr_jurnal RENAME COLUMN created_by TO created_by_id;

ALTER TABLE tr_jurnal
    ADD COLUMN IF NOT EXISTS status VARCHAR(10) NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'PENDING', 'POSTED', 'VOID')),
    ADD COLUMN IF NOT EXISTS submitted_by_id  INTEGER,
    ADD COLUMN IF NOT EXISTS approved_by_id   INTEGER,
    ADD COLUMN IF NOT EXISTS approved_at      TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS posted_at        TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS reversal_of_id   UUID REFERENCES tr_jurnal(id),
    ADD COLUMN IF NOT EXISTS fiscal_period_id INTEGER REFERENCES ms_periode_akuntansi(id),
    ADD COLUMN IF NOT EXISTS is_deleted       BOOLEAN NOT NULL DEFAULT FALSE;

-- Segregation of Duties: approver tidak boleh sama dengan pembuat
ALTER TABLE tr_jurnal
    ADD CONSTRAINT chk_sod
        CHECK (approved_by_id IS NULL OR approved_by_id <> created_by_id);

-- Data hasil migrasi ETL adalah historis final -> tandai POSTED
-- (dijalankan SEBELUM trigger dibuat agar tidak terblokir).
UPDATE tr_jurnal SET status = 'POSTED', posted_at = created_at WHERE status = 'DRAFT';

-- =========================================================
-- 3. tr_jurnal_detail: integritas
-- =========================================================
ALTER TABLE tr_jurnal_detail
    ALTER COLUMN jurnal_id SET NOT NULL,
    ALTER COLUMN kode_akun SET NOT NULL;

-- =========================================================
-- 4. tr_anggaran: anti-duplikat + carry over + periode
-- =========================================================
ALTER TABLE tr_anggaran
    ADD COLUMN IF NOT EXISTS carry_over BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS periode_id INTEGER REFERENCES ms_periode_akuntansi(id);

-- bulan boleh NULL (anggaran tahunan); COALESCE agar tetap unik
CREATE UNIQUE INDEX IF NOT EXISTS uq_anggaran
    ON tr_anggaran (kode_akun, tahun_anggaran, COALESCE(bulan, 0));

-- =========================================================
-- 5. AUDIT LOG (trigger-based, tamper-evident untuk core keuangan)
-- =========================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id         BIGSERIAL PRIMARY KEY,
    table_name TEXT        NOT NULL,
    row_pk     TEXT,
    action     VARCHAR(10) NOT NULL,
    old_data   JSONB,
    new_data   JSONB,
    changed_by INTEGER,                       -- user aplikasi (via app.current_user_id)
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION fn_audit() RETURNS TRIGGER AS $$
DECLARE
    v_user INTEGER;
    v_pk   TEXT;
BEGIN
    -- user aplikasi dikirim Django via: SET LOCAL app.current_user_id = '<id>'
    BEGIN
        v_user := NULLIF(current_setting('app.current_user_id', true), '')::INTEGER;
    EXCEPTION WHEN others THEN
        v_user := NULL;
    END;

    IF (TG_OP = 'DELETE') THEN
        v_pk := to_jsonb(OLD) ->> TG_ARGV[0];
        INSERT INTO audit_log(table_name, row_pk, action, old_data, new_data, changed_by)
        VALUES (TG_TABLE_NAME, v_pk, TG_OP, to_jsonb(OLD), NULL, v_user);
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        v_pk := to_jsonb(NEW) ->> TG_ARGV[0];
        INSERT INTO audit_log(table_name, row_pk, action, old_data, new_data, changed_by)
        VALUES (TG_TABLE_NAME, v_pk, TG_OP, to_jsonb(OLD), to_jsonb(NEW), v_user);
        RETURN NEW;
    ELSE
        v_pk := to_jsonb(NEW) ->> TG_ARGV[0];
        INSERT INTO audit_log(table_name, row_pk, action, old_data, new_data, changed_by)
        VALUES (TG_TABLE_NAME, v_pk, TG_OP, NULL, to_jsonb(NEW), v_user);
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =========================================================
-- 6. IMMUTABILITY: jurnal POSTED tidak boleh diubah/dihapus
--    (koreksi dilakukan via reversing entry)
-- =========================================================
CREATE OR REPLACE FUNCTION fn_protect_posted_jurnal() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        IF OLD.status = 'POSTED' THEN
            RAISE EXCEPTION 'Jurnal POSTED tidak boleh dihapus (gunakan reversal). id=%', OLD.id;
        END IF;
        RETURN OLD;
    END IF;

    IF OLD.status = 'POSTED' THEN
        IF NEW.status NOT IN ('POSTED', 'VOID') THEN
            RAISE EXCEPTION 'Jurnal POSTED hanya boleh berubah status ke VOID. id=%', OLD.id;
        END IF;
        IF NEW.tanggal <> OLD.tanggal OR NEW.no_bukti <> OLD.no_bukti
           OR NEW.created_by_id IS DISTINCT FROM OLD.created_by_id THEN
            RAISE EXCEPTION 'Field inti jurnal POSTED bersifat immutable. id=%', OLD.id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_protect_posted_detail() RETURNS TRIGGER AS $$
DECLARE v_status VARCHAR(10);
BEGIN
    IF (TG_OP = 'DELETE') THEN
        SELECT status INTO v_status FROM tr_jurnal WHERE id = OLD.jurnal_id;
        IF v_status = 'POSTED' THEN
            RAISE EXCEPTION 'Detail jurnal POSTED tidak boleh dihapus (gunakan reversal).';
        END IF;
        RETURN OLD;
    ELSE
        SELECT status INTO v_status FROM tr_jurnal WHERE id = NEW.jurnal_id;
        IF v_status = 'POSTED' THEN
            RAISE EXCEPTION 'Detail jurnal POSTED tidak boleh diubah (gunakan reversal).';
        END IF;
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =========================================================
-- 7. KONTROL ANGGARAN + PERIODE TERTUTUP (backstop DB, saat POST)
--    Service layer Django tetap validasi lebih dulu utk UX.
-- =========================================================
CREATE OR REPLACE FUNCTION fn_check_post_rules() RETURNS TRIGGER AS $$
DECLARE
    rec         RECORD;
    v_tahun     INTEGER;
    v_pagu      NUMERIC(18,2);
    v_realisasi NUMERIC(18,2);
    v_periode   RECORD;
BEGIN
    IF NEW.status = 'POSTED' AND OLD.status IS DISTINCT FROM 'POSTED' THEN
        -- a) tolak posting ke periode yang sudah CLOSED
        SELECT * INTO v_periode FROM ms_periode_akuntansi
        WHERE NEW.tanggal BETWEEN tgl_mulai AND tgl_selesai
        ORDER BY tgl_mulai DESC LIMIT 1;
        IF FOUND AND v_periode.status = 'CLOSED' THEN
            RAISE EXCEPTION 'Periode % sudah CLOSED, posting ditolak (tanggal=%).',
                v_periode.kode, NEW.tanggal;
        END IF;

        -- b) hard-block bila beban melampaui pagu anggaran
        v_tahun := EXTRACT(YEAR FROM NEW.tanggal)::INTEGER;
        FOR rec IN
            SELECT d.kode_akun, SUM(d.debit) AS debit_baru
            FROM tr_jurnal_detail d
            JOIN ms_coa c ON c.kode_akun = d.kode_akun
            WHERE d.jurnal_id = NEW.id
              AND substring(c.kode_akun FROM 1 FOR 1) = '5'   -- akun beban
            GROUP BY d.kode_akun
        LOOP
            -- kunci baris anggaran dulu (FOR UPDATE tak boleh dgn agregat),
            -- agar bebas dari race condition antar posting bersamaan
            PERFORM 1 FROM tr_anggaran
            WHERE kode_akun = rec.kode_akun AND tahun_anggaran = v_tahun
            FOR UPDATE;

            SELECT COALESCE(SUM(nominal_anggaran), 0) INTO v_pagu
            FROM tr_anggaran
            WHERE kode_akun = rec.kode_akun AND tahun_anggaran = v_tahun;

            IF v_pagu > 0 THEN
                SELECT COALESCE(SUM(d.debit - d.kredit), 0) INTO v_realisasi
                FROM tr_jurnal_detail d
                JOIN tr_jurnal j ON j.id = d.jurnal_id
                WHERE d.kode_akun = rec.kode_akun
                  AND j.status = 'POSTED' AND NOT j.is_deleted
                  AND EXTRACT(YEAR FROM j.tanggal) = v_tahun;

                IF (v_realisasi + rec.debit_baru) > v_pagu THEN
                    RAISE EXCEPTION
                        'Pagu anggaran terlampaui akun % thn %: pagu=%, realisasi=%, tambahan=%',
                        rec.kode_akun, v_tahun, v_pagu, v_realisasi, rec.debit_baru;
                END IF;
            END IF;
        END LOOP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =========================================================
-- 8. PASANG TRIGGER (dibuat terakhir, setelah data legacy disesuaikan)
-- =========================================================
DROP TRIGGER IF EXISTS trg_protect_jurnal ON tr_jurnal;
CREATE TRIGGER trg_protect_jurnal
    BEFORE UPDATE OR DELETE ON tr_jurnal
    FOR EACH ROW EXECUTE FUNCTION fn_protect_posted_jurnal();

DROP TRIGGER IF EXISTS trg_post_rules ON tr_jurnal;
CREATE TRIGGER trg_post_rules
    BEFORE UPDATE ON tr_jurnal
    FOR EACH ROW EXECUTE FUNCTION fn_check_post_rules();

DROP TRIGGER IF EXISTS trg_protect_detail ON tr_jurnal_detail;
CREATE TRIGGER trg_protect_detail
    BEFORE UPDATE OR DELETE ON tr_jurnal_detail
    FOR EACH ROW EXECUTE FUNCTION fn_protect_posted_detail();

-- Audit pada tabel core (PK dikirim sebagai argumen trigger)
DROP TRIGGER IF EXISTS trg_audit_golongan ON ms_golongan;
CREATE TRIGGER trg_audit_golongan AFTER INSERT OR UPDATE OR DELETE ON ms_golongan
    FOR EACH ROW EXECUTE FUNCTION fn_audit('id');
DROP TRIGGER IF EXISTS trg_audit_subgol ON ms_sub_golongan;
CREATE TRIGGER trg_audit_subgol AFTER INSERT OR UPDATE OR DELETE ON ms_sub_golongan
    FOR EACH ROW EXECUTE FUNCTION fn_audit('id');
DROP TRIGGER IF EXISTS trg_audit_coa ON ms_coa;
CREATE TRIGGER trg_audit_coa AFTER INSERT OR UPDATE OR DELETE ON ms_coa
    FOR EACH ROW EXECUTE FUNCTION fn_audit('kode_akun');
DROP TRIGGER IF EXISTS trg_audit_jurnal ON tr_jurnal;
CREATE TRIGGER trg_audit_jurnal AFTER INSERT OR UPDATE OR DELETE ON tr_jurnal
    FOR EACH ROW EXECUTE FUNCTION fn_audit('id');
DROP TRIGGER IF EXISTS trg_audit_jurnal_detail ON tr_jurnal_detail;
CREATE TRIGGER trg_audit_jurnal_detail AFTER INSERT OR UPDATE OR DELETE ON tr_jurnal_detail
    FOR EACH ROW EXECUTE FUNCTION fn_audit('id');
DROP TRIGGER IF EXISTS trg_audit_anggaran ON tr_anggaran;
CREATE TRIGGER trg_audit_anggaran AFTER INSERT OR UPDATE OR DELETE ON tr_anggaran
    FOR EACH ROW EXECUTE FUNCTION fn_audit('id');

-- =========================================================
-- 9. INDEXING
-- =========================================================
CREATE INDEX IF NOT EXISTS idx_jd_jurnal  ON tr_jurnal_detail (jurnal_id);
CREATE INDEX IF NOT EXISTS idx_jd_akun    ON tr_jurnal_detail (kode_akun);
CREATE INDEX IF NOT EXISTS idx_j_tanggal  ON tr_jurnal (tanggal);
CREATE INDEX IF NOT EXISTS idx_j_status   ON tr_jurnal (status);
CREATE INDEX IF NOT EXISTS idx_j_period   ON tr_jurnal (fiscal_period_id);

-- =========================================================
-- 10. PERBAIKAN VIEW: hanya jurnal POSTED & belum dihapus
-- =========================================================
DROP VIEW IF EXISTS v_neraca_saldo;
CREATE VIEW v_neraca_saldo AS
SELECT
    mc.kode_akun, mc.nama_akun, mc.posisi_normal,
    COALESCE(SUM(tjd.debit), 0)  AS total_debit,
    COALESCE(SUM(tjd.kredit), 0) AS total_kredit,
    CASE
        WHEN mc.posisi_normal = 'D' THEN COALESCE(SUM(tjd.debit - tjd.kredit), 0)
        ELSE COALESCE(SUM(tjd.kredit - tjd.debit), 0)
    END AS saldo_akhir
FROM ms_coa mc
LEFT JOIN tr_jurnal_detail tjd ON mc.kode_akun = tjd.kode_akun
    AND EXISTS (
        SELECT 1 FROM tr_jurnal tj
        WHERE tj.id = tjd.jurnal_id AND tj.status = 'POSTED' AND NOT tj.is_deleted
    )
GROUP BY mc.kode_akun, mc.nama_akun, mc.posisi_normal;

DROP VIEW IF EXISTS v_dataset_prediksi_kas;
CREATE VIEW v_dataset_prediksi_kas AS
SELECT
    TO_CHAR(tj.tanggal, 'YYYY-MM')     AS periode,
    EXTRACT(YEAR  FROM tj.tanggal)     AS tahun,
    EXTRACT(MONTH FROM tj.tanggal)     AS bulan,
    SUM(tjd.debit)                     AS arus_kas_masuk,
    SUM(tjd.kredit)                    AS arus_kas_keluar,
    SUM(tjd.debit - tjd.kredit)        AS net_cash_flow_bulanan
FROM tr_jurnal tj
JOIN tr_jurnal_detail tjd ON tj.id = tjd.jurnal_id
WHERE tj.status = 'POSTED' AND NOT tj.is_deleted
  AND (tjd.kode_akun LIKE '1.1.0%' OR tjd.kode_akun LIKE '1.2.0%')
GROUP BY 1, 2, 3
ORDER BY 1 ASC;

-- Anggaran vs realisasi (untuk dashboard "anggaran vs beban")
DROP VIEW IF EXISTS v_realisasi_anggaran;
CREATE VIEW v_realisasi_anggaran AS
SELECT
    a.kode_akun, c.nama_akun, a.tahun_anggaran,
    SUM(a.nominal_anggaran) AS pagu,
    COALESCE((
        SELECT SUM(d.debit - d.kredit)
        FROM tr_jurnal_detail d JOIN tr_jurnal j ON j.id = d.jurnal_id
        WHERE d.kode_akun = a.kode_akun AND j.status = 'POSTED' AND NOT j.is_deleted
          AND EXTRACT(YEAR FROM j.tanggal) = a.tahun_anggaran
    ), 0) AS realisasi,
    SUM(a.nominal_anggaran) - COALESCE((
        SELECT SUM(d.debit - d.kredit)
        FROM tr_jurnal_detail d JOIN tr_jurnal j ON j.id = d.jurnal_id
        WHERE d.kode_akun = a.kode_akun AND j.status = 'POSTED' AND NOT j.is_deleted
          AND EXTRACT(YEAR FROM j.tanggal) = a.tahun_anggaran
    ), 0) AS sisa_pagu
FROM tr_anggaran a
JOIN ms_coa c ON c.kode_akun = a.kode_akun
GROUP BY a.kode_akun, c.nama_akun, a.tahun_anggaran;

-- =========================================================
-- 11. PINDAH KEPEMILIKAN: ms_siswa & ms_pegawai -> Django ORM
--     (tabel ini kosong / tidak diisi ETL, aman di-drop)
-- =========================================================
DROP TABLE IF EXISTS ms_siswa CASCADE;
DROP TABLE IF EXISTS ms_pegawai CASCADE;

COMMIT;
