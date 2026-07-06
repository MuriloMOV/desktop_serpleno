#!/usr/bin/env python3
"""
Script para configurar os grupos necessários para o sistema de comunicação interna
"""

from ser_pleno.infrastructure.database import get_db_connection


def setup_groups():
    """Configura os grupos necessários (Gestores, Profissionais, Suporte) e adiciona usuários"""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Verifica se grupos existem
        cursor.execute("SELECT * FROM auth_group")
        grupos_existentes = cursor.fetchall()
        nomes_grupos = [g["name"] for g in grupos_existentes]

        # Cria grupos se não existem
        grupos_necessarios = ["Gestores", "Profissionais", "Suporte"]
        for grupo in grupos_necessarios:
            if grupo not in nomes_grupos:
                cursor.execute("INSERT INTO auth_group (name) VALUES (%s)", (grupo,))
                print(f"Grupo '{grupo}' criado com sucesso")

        connection.commit()

        # Verifica usuários e grupos
        cursor.execute("""
            SELECT u.username, u.id, g.name
            FROM auth_user u
            LEFT JOIN auth_user_groups ug ON u.id = ug.user_id
            LEFT JOIN auth_group g ON ug.group_id = g.id
        """)
        usuarios_grupos = cursor.fetchall()

        print("\nUsuários e grupos:")
        for ug in usuarios_grupos:
            print(f"Username: {ug['username']}, ID: {ug['id']}, Grupo: {ug['name']}")

        # Adiciona usuários 'coord.teste' e 'coord' ao grupo Gestores
        # Pesquisa IDs dos usuários
        cursor.execute("SELECT id, username FROM auth_user WHERE username IN ('coord.teste', 'coord')")
        coordenadores = cursor.fetchall()

        if coordenadores:
            cursor.execute("SELECT id FROM auth_group WHERE name = 'Gestores'")
            grupo_gestores = cursor.fetchone()

            if grupo_gestores:
                for coord in coordenadores:
                    # Verifica se já está no grupo
                    cursor.execute("""
                        SELECT * FROM auth_user_groups 
                        WHERE user_id = %s AND group_id = %s
                    """, (coord["id"], grupo_gestores["id"]))

                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO auth_user_groups (user_id, group_id) 
                            VALUES (%s, %s)
                        """, (coord["id"], grupo_gestores["id"]))
                        print(f"\nUsuário '{coord['username']}' adicionado ao grupo 'Gestores'")

        connection.commit()

        # Verifica novamente usuários e grupos
        cursor.execute("""
            SELECT u.username, u.id, g.name
            FROM auth_user u
            LEFT JOIN auth_user_groups ug ON u.id = ug.user_id
            LEFT JOIN auth_group g ON ug.group_id = g.id
            WHERE u.username IN ('coord.teste', 'coord')
        """)
        coord_grupos = cursor.fetchall()

        print("\nVerificação de coordenadores:")
        for cg in coord_grupos:
            print(f"Username: {cg['username']}, ID: {cg['id']}, Grupo: {cg['name']}")

    except Exception as e:
        print(f"Erro: {type(e).__name__}: {e}")
        connection.rollback()

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    print("Configuração de grupos para comunicação interna")
    print("=" * 50)
    setup_groups()
    print("\nConfiguração concluÍda!")
