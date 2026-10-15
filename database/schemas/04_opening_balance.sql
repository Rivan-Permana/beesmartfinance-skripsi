ALTER TABLE ms_coa ADD COLUMN saldo_awal NUMERIC(18,2) NOT NULL DEFAULT 0;
ALTER TABLE ms_coa ADD COLUMN tanggal_saldo_awal DATE;
ALTER TABLE ms_coa ADD CONSTRAINT coa_saldo_awal_tanggal
    CHECK (saldo_awal = 0 OR tanggal_saldo_awal IS NOT NULL);

CREATE FUNCTION fn_protect_opening_balance() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.saldo_awal <> 0 THEN
            RAISE EXCEPTION 'Akun dengan saldo awal bukan nol tidak dapat dihapus';
        END IF;
        RETURN OLD;
    END IF;
    IF TG_OP = 'UPDATE' AND NEW.saldo_awal IS NOT DISTINCT FROM OLD.saldo_awal
       AND NEW.tanggal_saldo_awal IS NOT DISTINCT FROM OLD.tanggal_saldo_awal
       AND NEW.posisi_normal = OLD.posisi_normal THEN
        RETURN NEW;
    END IF;
    IF TG_OP = 'UPDATE' AND EXISTS (
        SELECT 1 FROM ms_periode_akuntansi p WHERE p.status = 'CLOSED'
        AND OLD.tanggal_saldo_awal BETWEEN p.tgl_mulai AND p.tgl_selesai
    ) THEN
        RAISE EXCEPTION 'Saldo awal pada periode CLOSED tidak dapat diubah';
    END IF;
    IF EXISTS (
        SELECT 1 FROM ms_periode_akuntansi p WHERE p.status = 'CLOSED'
        AND NEW.tanggal_saldo_awal BETWEEN p.tgl_mulai AND p.tgl_selesai
    ) THEN
        RAISE EXCEPTION 'Saldo awal pada periode CLOSED tidak dapat diubah';
    END IF;
    IF EXISTS (
        SELECT 1 FROM tr_jurnal_detail d JOIN tr_jurnal j ON j.id = d.jurnal_id
        WHERE d.kode_akun = NEW.kode_akun AND j.status = 'POSTED' AND NOT j.is_deleted
        AND j.tanggal < NEW.tanggal_saldo_awal
    ) THEN
        RAISE EXCEPTION 'Tanggal saldo awal harus sebelum atau sama dengan transaksi POSTED pertama akun';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_protect_opening_balance BEFORE INSERT OR UPDATE OR DELETE ON ms_coa
    FOR EACH ROW EXECUTE FUNCTION fn_protect_opening_balance();

CREATE FUNCTION fn_check_opening_date() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'POSTED' THEN
        PERFORM c.kode_akun FROM ms_coa c
        JOIN tr_jurnal_detail d ON d.kode_akun = c.kode_akun
        WHERE d.jurnal_id = NEW.id ORDER BY c.kode_akun FOR SHARE OF c;
    END IF;
    IF NEW.status = 'POSTED' AND EXISTS (
        SELECT 1 FROM tr_jurnal_detail d JOIN ms_coa c ON c.kode_akun = d.kode_akun
        WHERE d.jurnal_id = NEW.id AND c.tanggal_saldo_awal > NEW.tanggal
    ) THEN
        RAISE EXCEPTION 'Tanggal jurnal tidak boleh sebelum tanggal saldo awal akun';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_opening_date BEFORE INSERT OR UPDATE ON tr_jurnal
    FOR EACH ROW EXECUTE FUNCTION fn_check_opening_date();

CREATE FUNCTION fn_check_detail_opening_date() RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM tr_jurnal WHERE id = NEW.jurnal_id AND status = 'POSTED') THEN
        PERFORM kode_akun FROM ms_coa WHERE kode_akun = NEW.kode_akun FOR SHARE;
        IF EXISTS (
            SELECT 1 FROM tr_jurnal j JOIN ms_coa c ON c.kode_akun = NEW.kode_akun
            WHERE j.id = NEW.jurnal_id AND j.tanggal < c.tanggal_saldo_awal
        ) THEN
            RAISE EXCEPTION 'Tanggal jurnal tidak boleh sebelum tanggal saldo awal akun';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_detail_opening_date BEFORE INSERT OR UPDATE ON tr_jurnal_detail
    FOR EACH ROW EXECUTE FUNCTION fn_check_detail_opening_date();

CREATE OR REPLACE VIEW v_neraca_saldo AS
WITH mutasi AS (
    SELECT d.kode_akun, SUM(d.debit) AS debit, SUM(d.kredit) AS kredit
    FROM tr_jurnal_detail d
    JOIN tr_jurnal j ON j.id = d.jurnal_id
    JOIN ms_coa c ON c.kode_akun = d.kode_akun
    WHERE j.status = 'POSTED' AND NOT j.is_deleted
      AND (c.tanggal_saldo_awal IS NULL OR j.tanggal >= c.tanggal_saldo_awal)
    GROUP BY d.kode_akun
)
SELECT c.kode_akun, c.nama_akun, c.posisi_normal,
    COALESCE(m.debit, 0) + GREATEST(CASE WHEN c.posisi_normal = 'D' THEN c.saldo_awal ELSE -c.saldo_awal END, 0) AS total_debit,
    COALESCE(m.kredit, 0) + GREATEST(CASE WHEN c.posisi_normal = 'K' THEN c.saldo_awal ELSE -c.saldo_awal END, 0) AS total_kredit,
    c.saldo_awal + CASE WHEN c.posisi_normal = 'D'
        THEN COALESCE(m.debit, 0) - COALESCE(m.kredit, 0)
        ELSE COALESCE(m.kredit, 0) - COALESCE(m.debit, 0) END AS saldo_akhir
FROM ms_coa c LEFT JOIN mutasi m ON m.kode_akun = c.kode_akun;
