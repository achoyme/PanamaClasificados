import os

env_path = '.env'

if not os.path.exists(env_path):
    print("❌ No se encontró el archivo .env")
    exit()

with open(env_path, 'r', encoding='utf-8') as file:
    content = file.read()

if 'FLASK_ENV=development' in content:
    new_content = content.replace('FLASK_ENV=development', 'FLASK_ENV=production')
    modo = "PRODUCCIÓN 🔴 (Escudos Anti-Fraude ACTIVADOS)"
elif 'FLASK_ENV=production' in content:
    new_content = content.replace('FLASK_ENV=production', 'FLASK_ENV=development')
    modo = "DESARROLLO 🟢 (Escudos Apagados para Pruebas)"
else:
    # Si no existe la variable, la añade al inicio como development
    new_content = "FLASK_ENV=development\n" + content
    modo = "DESARROLLO 🟢"

with open(env_path, 'w', encoding='utf-8') as file:
    file.write(new_content)

print("=========================================")
print(f"🔄 MODO CAMBIADO EXITOSAMENTE A: {modo}")
print("⚠️ IMPORTANTE: Recuerda apagar y volver a encender tu servidor (run.py) para que los cambios hagan efecto.")
print("=========================================")