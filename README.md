# Iron Body - Registro de Clases de Prueba

Dashboard web en Python con Streamlit conectado a Google Sheets como base de datos.

## Campos del registro

- Nombre
- Cédula
- Celular
- Horario
- Disciplina:
  - Pesas y cardio
  - TRX
  - Iron Reformer
  - Cycling
  - Jiujitsu

## Archivos incluidos

```text
app.py
requirements.txt
.gitignore
.streamlit/secrets.toml.example
README.md
```

## 1. Crear la credencial de Google Sheets

1. Entra a Google Cloud Console.
2. Crea un proyecto nuevo o usa uno existente.
3. Activa estas APIs:
   - Google Sheets API
   - Google Drive API
4. Crea una cuenta de servicio.
5. Genera una clave JSON para esa cuenta de servicio.
6. Copia el contenido del JSON dentro del formato de `.streamlit/secrets.toml.example`.

El correo de la cuenta de servicio se ve parecido a:

```text
nombre@proyecto.iam.gserviceaccount.com
```

Crea un Google Sheet manualmente, por ejemplo con el nombre:

```text
Iron Body - Clases de Prueba
```

Copia el ID del Sheet desde la URL. Ejemplo:

```text
https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit
```

Luego comparte ese Google Sheet con el correo de la cuenta de servicio como Editor.

## 2. Uso local

Instala las dependencias:

```bash
pip install -r requirements.txt
```

Crea el archivo de secretos local:

```bash
mkdir .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edita `.streamlit/secrets.toml` con los datos reales del JSON de Google Cloud y coloca el `spreadsheet_id` de tu Google Sheet.

Ejecuta la app:

```bash
streamlit run app.py
```

## 3. Subir a GitHub

No subas `.streamlit/secrets.toml` porque contiene datos privados. Ya está protegido en `.gitignore`.

Comandos recomendados:

```bash
git init
git add .
git commit -m "Sistema Iron Body clases de prueba"
git branch -M main
git remote add origin URL_DE_TU_REPOSITORIO
git push -u origin main
```

## 4. Publicar en Streamlit Cloud

1. Sube este proyecto a GitHub.
2. Entra a Streamlit Cloud.
3. Crea una nueva app desde el repositorio.
4. Main file path: `app.py`.
5. En App settings > Secrets, pega el contenido completo de tu `.streamlit/secrets.toml`.
6. Deploy.

## Importante

El archivo `.streamlit/secrets.toml.example` es solo una plantilla. Para funcionar debes usar tus credenciales reales de Google Cloud.
