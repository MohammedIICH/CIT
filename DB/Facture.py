from DB.Initialisation import get_connection
from sqlite3 import IntegrityError

class Facture:
    @staticmethod
    def _verifier_dates_et_quantites(cmd_id, date_fact, quantites, fact_id_exclu=None):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT date_cmd FROM commandes WHERE id = ?", (cmd_id,))
        commande = cur.fetchone()
        if not commande:
            conn.close()
            raise ValueError("Commande associée introuvable.")
        date_cmd = commande["date_cmd"]
        if date_fact < date_cmd:
            conn.close()
            raise ValueError("La date de la facture ne peut pas être antérieure à la date de la commande.")
        cur.execute("SELECT MAX(date_bl) AS max_date_bl FROM bls WHERE cmd_id = ?", (cmd_id,))
        max_bl = cur.fetchone()
        max_date_bl = max_bl["max_date_bl"]
        if max_date_bl is not None and date_fact > max_date_bl:
            conn.close()
            raise ValueError("La date de la facture ne peut pas être postérieure à la date du BL le plus récent.")
        excl_clause = ""
        params = [cmd_id]
        if fact_id_exclu is not None:
            excl_clause = "AND f.id != ?"
            params.append(fact_id_exclu)
        cur.execute(f"""
            SELECT fi.produit, SUM(COALESCE(bi.qte_livree, 0)) AS qte_livree_totale
            FROM facture_items fi
            LEFT JOIN factures f ON fi.fact_id = f.id
            LEFT JOIN bl_items bi ON bi.produit = fi.produit
            LEFT JOIN bls b ON bi.bl_id = b.id AND b.cmd_id = f.cmd_id
            WHERE f.cmd_id = ? {excl_clause}
            GROUP BY fi.produit
        """, params)
        qtes_livrees = {row["produit"]: row["qte_livree_totale"] or 0 for row in cur.fetchall()}
        for prod, qte_fact in quantites.items():
            qte_livree = qtes_livrees.get(prod, 0)
            if qte_fact < qte_livree:
                conn.close()
                raise ValueError(f"La quantité facturée pour le produit '{prod}' ({qte_fact}) est inférieure à la quantité déjà livrée ({qte_livree}).")
        conn.close()

    @staticmethod
    def creer(cmd_id, numero, date, quantites):
        Facture._verifier_dates_et_quantites(cmd_id, date, quantites)
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO factures (cmd_id, numero, date_fact) VALUES (?, ?, ?)",
                (cmd_id, numero, date)
            )
            fact_id = cur.lastrowid
            for prod, qte in quantites.items():
                if qte > 0:
                    cur.execute(
                        "INSERT INTO facture_items (fact_id, produit, qte_cmd) VALUES (?, ?, ?)",
                        (fact_id, prod, qte)
                    )
            conn.commit()
            return fact_id
        except IntegrityError as e:
            conn.rollback()
            msg = str(e)
            if "UNIQUE constraint failed: factures.numero" in msg:
                raise ValueError("Ce numéro de facture existe déjà.")
            elif "FOREIGN KEY constraint failed" in msg:
                raise ValueError("Un des produits spécifiés n'existe pas dans la base de données.")
            else:
                raise
        finally:
            conn.close()

    @staticmethod
    def ajouter_produit(fact_id, produit, qte_cmd):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO facture_items (fact_id, produit, qte_cmd) VALUES (?, ?, ?)",
                (fact_id, produit, qte_cmd)
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_par_commande(cmd_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM factures WHERE cmd_id = ?", (cmd_id,))
        facture = cur.fetchone()
        conn.close()
        return facture

    @staticmethod
    def get_produits_facture(fact_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT produit, qte_cmd FROM facture_items WHERE fact_id = ?",
            (fact_id,)
        )
        items = cur.fetchall()
        conn.close()
        return {item["produit"]: item["qte_cmd"] for item in items}

    @staticmethod
    def mettre_a_jour(fact_id, numero, date, quantites):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT cmd_id FROM factures WHERE id = ?", (fact_id,))
        fact = cur.fetchone()
        if not fact:
            conn.close()
            raise ValueError("Facture introuvable.")
        cmd_id = fact["cmd_id"]
        Facture._verifier_dates_et_quantites(cmd_id, date, quantites, fact_id_exclu=fact_id)
        try:
            cur.execute(
                "UPDATE factures SET numero = ?, date_fact = ? WHERE id = ?",
                (numero, date, fact_id)
            )
            cur.execute("DELETE FROM facture_items WHERE fact_id = ?", (fact_id,))
            for prod, qte in quantites.items():
                if qte > 0:
                    cur.execute(
                        "INSERT INTO facture_items (fact_id, produit, qte_cmd) VALUES (?, ?, ?)",
                        (fact_id, prod, qte)
                    )
            conn.commit()
        except IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: factures.numero" in str(e):
                raise ValueError("Un autre numéro de facture existe déjà.")
            raise
        finally:
            conn.close()

    @staticmethod
    def supprimer(fact_id):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT cmd_id FROM factures WHERE id = ?", (fact_id,))
            fact = cur.fetchone()
            if not fact:
                conn.close()
                raise ValueError("Facture introuvable.")

            cmd_id = fact["cmd_id"]

            cur.execute("DELETE FROM bls WHERE cmd_id = ?", (cmd_id,))
            cur.execute("DELETE FROM factures WHERE id = ?", (fact_id,))
            cur.execute("DELETE FROM soldes_dus WHERE cmd_id = ?", (cmd_id,))
            cur.execute("UPDATE commandes SET status = 'En cours' WHERE id = ?", (cmd_id,))
            
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_par_numero(numero):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM factures WHERE numero = ?", (numero,))
        fac = cur.fetchone()
        conn.close()
        return fac
