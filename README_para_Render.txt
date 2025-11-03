IA Multisuministros de Costa Rica - Paquete para GitHub/Render
--------------------------------------------------------------
Contenido:
- IA_Multisuministros.py
- codigos_multisuministros.db
- requirements.txt
- assets/logo.png
- backup_instrucciones.txt
- README_para_Render.txt

Subida a GitHub:
1) Crear repositorio nuevo (ej. IA-Multisuministros)
2) Subir TODOS los archivos y carpetas descomprimidos (no subas el .zip)
3) Commit y push

Despliegue en Render:
1) En Render -> New -> Web Service -> GitHub -> seleccionar repo
2) Build command: pip install -r requirements.txt
3) Start command: streamlit run IA_Multisuministros.py --server.port=$PORT --server.address=0.0.0.0
4) Crear servicio y esperar URL pública

Credenciales iniciales:
- admin / admin123 (cambiar al ingresar)
