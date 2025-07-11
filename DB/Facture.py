from DB.Initialisation import get_connection

class Facture:
    @staticmethod
    def creer(cmd_id, numero, date, quantites):
        conn = get_connection()
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
        conn.close()

    @staticmethod
    def ajouter_produit(fact_id, produit, qte_cmd):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO facture_items (fact_id, produit, qte_cmd) VALUES (?, ?, ?)",
            (fact_id, produit, qte_cmd)
        )
        conn.commit()
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
        conn.close()

    @staticmethod
    def supprimer(fact_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM facture_items WHERE fact_id = ?", (fact_id,))
        cur.execute("DELETE FROM factures WHERE id = ?", (fact_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_par_numero(numero):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM factures WHERE numero = ?", (numero,))
        fac = cur.fetchone()
        conn.close()
        return fac
