from DB.Initialisation import get_connection

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
        cur = conn.cursor()
        cur.execute("INSERT INTO produits (nom) VALUES (?)", (nom,))
        conn.commit()
        conn.close()

    @staticmethod
    def supprimer(nom):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM produits WHERE nom = ?", (nom,))
        conn.commit()
        conn.close()

    @staticmethod
    def renommer(ancien_nom, nouveau_nom):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE produits SET nom = ? WHERE nom = ?", (nouveau_nom, ancien_nom))
        conn.commit()
        conn.close()

    @staticmethod
    def existe(nom):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM produits WHERE nom = ?", (nom,))
        res = cur.fetchone()
        conn.close()
        return res is not None
