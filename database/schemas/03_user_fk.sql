-- File: database/schemas/03_user_fk.sql
-- Menambahkan FK dari kolom user di core ke tabel custom user Django (accounts_user).
-- PRASYARAT: jalankan SETELAH app Django `accounts` di-migrate sehingga
--            tabel accounts_user sudah ada.
--
-- Pada DB produksi yang sudah berisi data ETL, urutannya:
--   1) jalankan 01_init_schema.sql  (sudah)
--   2) jalankan 02_governance.sql
--   3) Django: migrate app `accounts` (membuat accounts_user)
--   4) jalankan 03_user_fk.sql  <-- file ini

BEGIN;

ALTER TABLE tr_jurnal
    ADD CONSTRAINT fk_jurnal_created_by
        FOREIGN KEY (created_by_id)   REFERENCES accounts_user(id),
    ADD CONSTRAINT fk_jurnal_submitted_by
        FOREIGN KEY (submitted_by_id) REFERENCES accounts_user(id),
    ADD CONSTRAINT fk_jurnal_approved_by
        FOREIGN KEY (approved_by_id)  REFERENCES accounts_user(id);

ALTER TABLE audit_log
    ADD CONSTRAINT fk_audit_changed_by
        FOREIGN KEY (changed_by) REFERENCES accounts_user(id);

COMMIT;
