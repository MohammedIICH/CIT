from DB.Initialisation import get_connection
from sqlite3 import IntegrityError

class BonLivraison:
    @staticmethod
    def _verifier_facture_existante(cmd_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, date_fact FROM factures WHERE cmd_id = ?", (cmd_id,))
        facture = cur.fetchone()
        conn.close()
        if facture is None:
            raise ValueError("Impossible de créer un BL sans facture existante pour cette commande.")
        return facture

    @staticmethod
    def _verifier_date(date_bl, date_fact):
        if date_bl < date_fact:
            raise ValueError("La date du BL ne peut pas être antérieure à la date de la facture.")

    @staticmethod
    def _verifier_quantites(cmd_id, quantites, bl_id_exclu=None):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT fi.produit, fi.qte_cmd
            FROM facture_items fi
            JOIN factures f ON fi.fact_id = f.id
            WHERE f.cmd_id = ?
        """, (cmd_id,))
        qtes_facturees = {row["produit"]: row["qte_cmd"] for row in cur.fetchall()}
        if bl_id_exclu is None:
            excl_clause = ""
            params = (cmd_id,)
        else:
            excl_clause = "AND b.id != ?"
            params = (cmd_id, bl_id_exclu)
        cur.execute(f"""
            SELECT bi.produit, SUM(bi.qte_livree) as qte_livree_totale
            FROM bl_items bi
            JOIN bls b ON bi.bl_id = b.id
            WHERE b.cmd_id = ? {excl_clause}
            GROUP BY bi.produit
        """, params)
        qtes_livrees = {row["produit"]: row["qte_livree_totale"] for row in cur.fetchall()}
        for prod, qte_nouvelle in quantites.items():
            if qte_nouvelle < 0:
                raise ValueError(f"La quantité livrée pour le produit '{prod}' ne peut pas être négative.")
            qte_facturee = qtes_facturees.get(prod, 0)
            qte_livree = qtes_livrees.get(prod, 0)
            qte_totale = qte_livree + qte_nouvelle
            if qte_totale > qte_facturee:
                raise ValueError(f"La quantité totale livrée pour '{prod}' ({qte_totale}) dépasse la quantité facturée ({qte_facturee}).")
        conn.close()

    @staticmethod
    def creer(cmd_id, numero_bl, date_bl, quantites):
        facture = BonLivraison._verifier_facture_existante(cmd_id)
        BonLivraison._verifier_date(date_bl, facture["date_fact"])
        BonLivraison._verifier_quantites(cmd_id, quantites)
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO bls (cmd_id, numero_bl, date_bl) VALUES (?, ?, ?)",
                (cmd_id, numero_bl, date_bl)
            )
            bl_id = cur.lastrowid
            for prod, qte in quantites.items():
                if qte > 0:
                    cur.execute(
                        "INSERT INTO bl_items (bl_id, produit, qte_livree) VALUES (?, ?, ?)",
                        (bl_id, prod, qte)
                    )
            conn.commit()
            return bl_id
        except IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: bls.numero_bl" in str(e):
                raise ValueError("Ce numéro de BL existe déjà !")
            raise
        finally:
            conn.close()

    @staticmethod
    def mettre_a_jour(bl_id, numero_bl, date_bl, quantites):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT cmd_id FROM bls WHERE id = ?", (bl_id,))
        bl = cur.fetchone()
        if not bl:
            conn.close()
            raise ValueError("BL à mettre à jour introuvable.")
        cmd_id = bl["cmd_id"]
        cur.execute("SELECT date_fact FROM factures WHERE cmd_id = ?", (cmd_id,))
        facture = cur.fetchone()
        conn.close()
        if not facture:
            raise ValueError("Facture associée introuvable.")
        BonLivraison._verifier_date(date_bl, facture["date_fact"])
        BonLivraison._verifier_quantites(cmd_id, quantites, bl_id_exclu=bl_id)
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE bls SET numero_bl = ?, date_bl = ? WHERE id = ?",
                (numero_bl, date_bl, bl_id)
            )
            cur.execute("DELETE FROM bl_items WHERE bl_id = ?", (bl_id,))
            for prod, qte in quantites.items():
                if qte > 0:
                    cur.execute(
                        "INSERT INTO bl_items (bl_id, produit, qte_livree) VALUES (?, ?, ?)",
                        (bl_id, prod, qte)
                    )
            conn.commit()
        except IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: bls.numero_bl" in str(e):
                raise ValueError("Ce numéro de BL existe déjà !")
            raise
        finally:
            conn.close()

    @staticmethod
    def get_par_commande(cmd_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM bls WHERE cmd_id = ? ORDER BY date_bl", (cmd_id,))
        bls = cur.fetchall()
        conn.close()
        return bls

    @staticmethod
    def get_produits_bl(bl_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT produit, qte_livree FROM bl_items WHERE bl_id = ?", (bl_id,))
        items = cur.fetchall()
        conn.close()
        return {item["produit"]: item["qte_livree"] for item in items}

    @staticmethod
    def supprimer(bl_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM bl_items WHERE bl_id = ?", (bl_id,))
        cur.execute("DELETE FROM bls WHERE id = ?", (bl_id,))
        conn.commit()
        conn.close()
