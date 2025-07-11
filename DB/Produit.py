from DB.Initialisation import get_connection
from sqlite3 import IntegrityError

class Produit:
    @staticmethod
    def get_tous():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT nom FROM produits ORDER BY nom")
        res = [row["nom"] for row in cur.fetchall()]
        conn.close()
        return res

    @staticmethod
    def ajouter(nom):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO produits (nom) VALUES (?)", (nom,))
            conn.commit()
        except IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: produits.nom" in str(e):
                raise ValueError("Ce produit existe déjà.")
            raise
        finally:
            conn.close()

    @staticmethod
    def supprimer(nom):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM facture_items WHERE produit = ? LIMIT 1", (nom,))
        if cur.fetchone():
            conn.close()
            raise ValueError("Impossible de supprimer : produit présent dans une facture.")
        cur.execute("SELECT 1 FROM bl_items WHERE produit = ? LIMIT 1", (nom,))
        if cur.fetchone():
            conn.close()
            raise ValueError("Impossible de supprimer : produit présent dans un bon de livraison.")
        cur.execute("DELETE FROM produits WHERE nom = ?", (nom,))
        conn.commit()
        conn.close()

    @staticmethod
    def renommer(ancien_nom, nouveau_nom):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM produits WHERE nom = ?", (nouveau_nom,))
            if cur.fetchone():
                raise ValueError("Le nouveau nom de produit existe déjà.")
            cur.execute("UPDATE produits SET nom = ? WHERE nom = ?", (nouveau_nom, ancien_nom))
            cur.execute("UPDATE facture_items SET produit = ? WHERE produit = ?", (nouveau_nom, ancien_nom))
            cur.execute("UPDATE bl_items SET produit = ? WHERE produit = ?", (nouveau_nom, ancien_nom))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def existe(nom):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM produits WHERE nom = ?", (nom,))
        res = cur.fetchone()
        conn.close()
        return res is not None
