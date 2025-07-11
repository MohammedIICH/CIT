from DB.Initialisation import get_connection
from sqlite3 import IntegrityError

class Commande:
    @staticmethod
    def _verifier_date_cmd_valide(nouveau_num, nouvelle_date):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT f.date_fact 
            FROM commandes c
            LEFT JOIN factures f ON f.cmd_id = c.id
            WHERE c.numero = ?
        """, (nouveau_num,))
        facture = cur.fetchone()
        conn.close()
        if facture and facture["date_fact"] is not None:
            if nouvelle_date < facture["date_fact"]:
                raise ValueError("La date de la commande ne peut pas être antérieure à la date de la facture associée.")

    @staticmethod
    def creer(numero, date_cmd):
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS total FROM produits")
            if cur.fetchone()["total"] == 0:
                raise ValueError("Impossible de créer une commande : aucun produit n'est encore ajouté.")
            Commande._verifier_date_cmd_valide(numero, date_cmd)
            try:
                cur.execute(
                    "INSERT INTO commandes (numero, date_cmd) VALUES (?, ?)",
                    (numero, date_cmd)
                )
            except IntegrityError as e:
                if "UNIQUE constraint failed: commandes.numero" in str(e):
                    raise ValueError("Une commande avec ce numéro existe déjà.")
                raise

    @staticmethod
    def get_par_id(id_commande):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM commandes WHERE id = ?", (id_commande,))
        commande = cursor.fetchone()
        conn.close()
        return commande

    @staticmethod
    def get_par_numero(numero):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM commandes WHERE numero = ?", (numero,))
        commande = cursor.fetchone()
        conn.close()
        return commande

    @staticmethod
    def get_toutes():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM commandes ORDER BY date_cmd DESC")
        commandes = cursor.fetchall()
        conn.close()
        return commandes

    @staticmethod
    def supprimer(id_commande):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM commandes WHERE id = ?", (id_commande,))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def mettre_a_jour(cmd_id, nouveau_num, nouvelle_date):
        Commande._verifier_date_cmd_valide(nouveau_num, nouvelle_date)
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE commandes SET numero = ?, date_cmd = ? WHERE id = ?",
                (nouveau_num, nouvelle_date, cmd_id)
            )
            conn.commit()
        except IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: commandes.numero" in str(e):
                raise ValueError("Une autre commande avec ce numéro existe déjà.")
            raise
        finally:
            conn.close()
