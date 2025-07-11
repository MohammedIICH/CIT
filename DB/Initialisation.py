import sqlite3

DB_NAME = "data.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS commandes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE NOT NULL,
            date_cmd DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'En cours'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS factures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cmd_id INTEGER NOT NULL UNIQUE,
            numero TEXT UNIQUE NOT NULL,
            date_fact DATE NOT NULL,
            FOREIGN KEY(cmd_id) REFERENCES commandes(id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS facture_items (
            fact_id INTEGER NOT NULL,
            produit TEXT NOT NULL,
            qte_cmd INTEGER NOT NULL DEFAULT 0 CHECK(qte_cmd >= 0),
            PRIMARY KEY(fact_id, produit),
            FOREIGN KEY(fact_id) REFERENCES factures(id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS bls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cmd_id INTEGER NOT NULL,
            numero_bl TEXT UNIQUE NOT NULL,
            date_bl DATE NOT NULL,
            FOREIGN KEY(cmd_id) REFERENCES commandes(id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS bl_items (
            bl_id INTEGER NOT NULL,
            produit TEXT NOT NULL,
            qte_livree INTEGER NOT NULL DEFAULT 0 CHECK(qte_livree >= 0),
            PRIMARY KEY(bl_id, produit),
            FOREIGN KEY(bl_id) REFERENCES bls(id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS solde_items (
            cmd_id INTEGER NOT NULL,
            produit TEXT NOT NULL,
            solde INTEGER NOT NULL,
            PRIMARY KEY(cmd_id, produit),
            FOREIGN KEY(cmd_id) REFERENCES commandes(id) ON DELETE CASCADE
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS produits (
            nom TEXT PRIMARY KEY
        )
    """)

    c.executescript("""
    CREATE TRIGGER IF NOT EXISTS trg_init_or_update_solde_after_facture
    AFTER INSERT ON facture_items
    BEGIN
      INSERT OR REPLACE INTO solde_items(cmd_id, produit, solde)
      VALUES(
        (SELECT cmd_id FROM factures WHERE id = NEW.fact_id),
        NEW.produit,
        NEW.qte_cmd - COALESCE(
          (SELECT SUM(bi.qte_livree)
           FROM bl_items bi
           JOIN bls b ON bi.bl_id = b.id
           WHERE b.cmd_id = (SELECT cmd_id FROM factures WHERE id = NEW.fact_id)
             AND bi.produit = NEW.produit
          ), 0
        )
      );
    END;

    CREATE TRIGGER IF NOT EXISTS trg_update_solde_after_facture_update
    AFTER UPDATE ON facture_items
    BEGIN
      UPDATE solde_items
      SET solde = NEW.qte_cmd - COALESCE(
        (SELECT SUM(bi.qte_livree)
         FROM bl_items bi
         JOIN bls b ON bi.bl_id = b.id
         WHERE b.cmd_id = (SELECT cmd_id FROM factures WHERE id = NEW.fact_id)
           AND bi.produit = NEW.produit
        ), 0
      )
      WHERE cmd_id = (SELECT cmd_id FROM factures WHERE id = NEW.fact_id)
        AND produit = NEW.produit;
    END;

    CREATE TRIGGER IF NOT EXISTS trg_update_solde_after_bl_ins
    AFTER INSERT ON bl_items
    BEGIN
      UPDATE solde_items
      SET solde = solde - NEW.qte_livree
      WHERE cmd_id = (SELECT cmd_id FROM bls WHERE id = NEW.bl_id)
        AND produit = NEW.produit;
    END;

    CREATE TRIGGER IF NOT EXISTS trg_update_solde_after_bl_upd
    AFTER UPDATE ON bl_items
    BEGIN
      UPDATE solde_items
      SET solde = solde + OLD.qte_livree - NEW.qte_livree
      WHERE cmd_id = (SELECT cmd_id FROM bls WHERE id = NEW.bl_id)
        AND produit = NEW.produit;
    END;

    CREATE TRIGGER IF NOT EXISTS trg_update_solde_after_bl_delete
    AFTER DELETE ON bl_items
    BEGIN
      UPDATE solde_items
      SET solde =
        COALESCE(
          (SELECT qte_cmd FROM facture_items
           WHERE fact_id = (
             SELECT id FROM factures WHERE cmd_id = (SELECT cmd_id FROM bls WHERE id = OLD.bl_id)
           ) AND produit = OLD.produit
          ), 0)
        - COALESCE(
          (SELECT SUM(qte_livree) FROM bl_items
           WHERE bl_id IN (
             SELECT id FROM bls WHERE cmd_id = (SELECT cmd_id FROM bls WHERE id = OLD.bl_id)
           )
           AND produit = OLD.produit
          ), 0
        )
      WHERE cmd_id = (SELECT cmd_id FROM bls WHERE id = OLD.bl_id)
        AND produit = OLD.produit;
    END;

    CREATE TRIGGER IF NOT EXISTS trg_delete_solde_if_no_factureitem
    AFTER DELETE ON facture_items
    BEGIN
      DELETE FROM solde_items
      WHERE cmd_id = (SELECT cmd_id FROM factures WHERE id = OLD.fact_id)
        AND produit = OLD.produit
        AND NOT EXISTS (SELECT 1 FROM facture_items WHERE fact_id = OLD.fact_id AND produit = OLD.produit);
    END;

    CREATE TRIGGER IF NOT EXISTS trg_update_solde_after_facture_delete
    AFTER DELETE ON facture_items
    BEGIN
      UPDATE solde_items
      SET solde = 
        COALESCE(
          (SELECT qte_cmd FROM facture_items
           WHERE fact_id = OLD.fact_id AND produit = OLD.produit
          ), 0)
        - COALESCE(
          (SELECT SUM(bi.qte_livree)
           FROM bl_items bi
           JOIN bls b ON bi.bl_id = b.id
           WHERE b.cmd_id = (SELECT cmd_id FROM factures WHERE id = OLD.fact_id)
             AND bi.produit = OLD.produit
          ), 0
        )
      WHERE cmd_id = (SELECT cmd_id FROM factures WHERE id = OLD.fact_id)
        AND produit = OLD.produit;
    END;

    CREATE TRIGGER IF NOT EXISTS trg_sync_commande_status
    AFTER INSERT ON solde_items
    BEGIN
      UPDATE commandes
      SET status =
        CASE
          WHEN NOT EXISTS (
            SELECT 1 FROM solde_items si
            WHERE si.cmd_id = NEW.cmd_id
              AND si.solde != 0
          ) THEN 'Livrée'
          ELSE 'En cours'
        END
      WHERE id = NEW.cmd_id;
    END;

    CREATE TRIGGER IF NOT EXISTS trg_sync_commande_status_update
    AFTER UPDATE ON solde_items
    BEGIN
      UPDATE commandes
      SET status =
        CASE
          WHEN NOT EXISTS (
            SELECT 1 FROM solde_items si
            WHERE si.cmd_id = NEW.cmd_id
              AND si.solde != 0
          ) THEN 'Livrée'
          ELSE 'En cours'
        END
      WHERE id = NEW.cmd_id;
    END;

    CREATE TRIGGER IF NOT EXISTS trg_sync_commande_status_delete
    AFTER DELETE ON solde_items
    BEGIN
      UPDATE commandes
      SET status =
        CASE
          WHEN NOT EXISTS (
            SELECT 1 FROM solde_items si
            WHERE si.cmd_id = OLD.cmd_id
              AND si.solde != 0
          ) THEN 'Livrée'
          ELSE 'En cours'
        END
      WHERE id = OLD.cmd_id;
    END;
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de données initialisée")
