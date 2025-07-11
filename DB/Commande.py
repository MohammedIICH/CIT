from DB.Initialisation import get_connection

class Commande:
    @staticmethod
    def creer(numero, date_cmd):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO commandes (numero, date_cmd)
            VALUES (?, ?)
        """, (numero, date_cmd))
        conn.commit()
        conn.close()

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
        cursor = conn.cursor()
        cursor.execute("DELETE FROM commandes WHERE id = ?", (id_commande,))
        conn.commit()
        conn.close()

    @staticmethod
    def mettre_a_jour(cmd_id, nouveau_num, nouvelle_date):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE commandes SET numero = ?, date_cmd = ? WHERE id = ?",
            (nouveau_num, nouvelle_date, cmd_id)
        )
        conn.commit()
        conn.close()
