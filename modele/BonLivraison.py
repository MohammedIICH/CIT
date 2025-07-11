from DataBase.Initialisation import get_connection
from sqlite3 import IntegrityError

class BonLivraison:
    @staticmethod
    def creer(cmd_id, numero_bl, date_bl, quantites):
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
            if "UNIQUE constraint failed: bls.numero_bl" in str(e):
                raise ValueError("Ce numéro de BL existe déjà !")
            else:
                raise
        finally:
            conn.close()

    @staticmethod
    def mettre_a_jour(bl_id, numero_bl, date_bl, quantites):
        conn = get_connection()
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
