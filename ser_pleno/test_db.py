#!/usr/bin/env python3
from config.db_config import get_db_connection

print("=== Verificando usuários no banco de dados ===")
conn = get_db_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT id, username, first_name, last_name, is_superuser, is_staff FROM auth_user ORDER BY id")
usuarios = cursor.fetchall()

for usuario in usuarios:
    tipo = "Admin" if usuario["is_superuser"] else "Staff" if usuario["is_staff"] else "Aluno"
    print(f"ID: {usuario['id']} - {usuario['first_name']} {usuario['last_name']} ({usuario['username']}) - {tipo}")

cursor.close()
conn.close()

print(f"\nTotal de usuários: {len(usuarios)}")
