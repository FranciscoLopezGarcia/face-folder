# Face Folder

Clasificador local de fotografías por persona, pensado para eventos y grandes
colecciones. Detecta caras, genera embeddings faciales y agrupa apariciones de
una misma persona en carpetas `atleta_001`, `atleta_002`, etc. Los casos que no
puede asignar con suficiente confianza quedan en `revision`.

El análisis se realiza en la computadora. **Los originales nunca se borran, se
mueven ni se modifican:** el programa sólo crea copias dentro de una nueva
carpeta de salida.

## Ejemplo

Entrada:

```text
evento/
├── IMG_001.jpg
├── IMG_002.jpg
└── IMG_003.cr3
```

Comando:

```bash
python sort_faces.py evento
```

Salida:

```text
evento/
└── resultado/
    ├── atleta_001/
    ├── atleta_002/
    └── revision/
```

Si `resultado` ya existe, la ejecución siguiente crea `resultado_2`, luego
`resultado_3`, y así sucesivamente. El programa excluye esas carpetas del
análisis para no procesar sus propias copias.

## Requisitos

- Windows 10/11 de 64 bits o macOS Apple Silicon.
- Python 3.10 o posterior.
- Internet durante la instalación y la primera descarga del modelo.
- Espacio libre para el entorno, el modelo y las copias de las fotos.

El procesamiento usa CPU. No requiere Docker, GPU, servicios cloud ni cuentas.

## Instalación en Windows

1. Instala Python desde [python.org](https://www.python.org/downloads/) y marca
   **Add Python to PATH** durante la instalación.
2. Descarga o clona este repositorio y abre una terminal en su carpeta.
3. Ejecuta:

   ```bat
   install_windows.bat
   ```

El instalador comprueba Python, crea `.venv`, instala `requirements.txt` y
descarga/verifica `buffalo_l`. Después puedes ejecutar:

```bat
start_windows.bat "C:\Fotos\Evento"
```

También puedes hacer doble clic en `start_windows.bat` y escribir o arrastrar
la carpeta cuando la solicite.

## Instalación en macOS

Abre Terminal en la carpeta del proyecto y ejecuta:

```bash
bash install.command
```

El instalador comprueba Python, crea `.venv`, instala las dependencias y
descarga/verifica `buffalo_l`. Para procesar una carpeta:

```bash
bash start.command "/Users/tu_usuario/Fotos/Evento"
```

En Apple Silicon se utiliza ONNX Runtime sobre CPU para mantener el mismo
comportamiento que en Windows.

## Uso

Con el entorno activado:

```bash
python sort_faces.py /ruta/al/evento
python sort_faces.py /ruta/al/evento /ruta/de/salida
python sort_faces.py --help
```

En Windows, sin activar el entorno:

```bat
.venv\Scripts\python.exe sort_faces.py "C:\Fotos\Evento" "D:\Clasificadas"
```

En macOS, sin activar el entorno:

```bash
.venv/bin/python sort_faces.py "/Volumes/Fotos/Evento" "/Volumes/Salida"
```

La CLI informa fotos encontradas, avance, caras detectadas, personas agrupadas,
cantidad enviada a revisión y ruta final.

## Formatos soportados

- Imágenes: `.jpg`, `.jpeg`, `.png`.
- RAW: `.cr2`, `.cr3`, `.nef`, `.arw`, `.raf`, `.dng`.

Para RAW se intenta analizar la vista previa incrustada; si es insuficiente, se
revela una versión reducida para el análisis. Siempre se copia el RAW original.
Otros formatos no se procesan.

## Cómo funciona

```text
detección de caras → embeddings ArcFace → filtro de calidad
→ clustering HDBSCAN → copia a carpetas
```

El paquete `buffalo_l` de InsightFace usa SCRFD para detectar caras y ArcFace
para obtener embeddings. HDBSCAN agrupa embeddings similares sin pedir de
antemano cuántas personas aparecen. Caras pequeñas, borrosas, de baja confianza
o sin grupo estable se envían a `revision`.

Una foto con varias personas puede copiarse a más de una carpeta. Esto requiere
más espacio, pero evita perder apariciones.

## Seguridad de los originales

`sort_faces.py` abre las fotos en modo lectura y usa `shutil.copy2` para crear
las salidas. No contiene operaciones para borrar, mover, renombrar o sobrescribir
originales. Una foto corrupta o un RAW incompatible se informa y se deriva a
`revision` sin detener el resto del lote.

## Rendimiento

La primera ejecución tarda más porque descarga e inicializa los modelos. El
tiempo total depende de la cantidad y resolución de las fotos, del formato RAW,
del almacenamiento y de la CPU. No se publican benchmarks porque variarían
demasiado entre equipos.

## Limitaciones

- Los perfiles, oclusiones, movimiento, mala iluminación y caras pequeñas
  reducen la precisión.
- Personas muy parecidas pueden mezclarse y una misma persona puede separarse
  en varios grupos.
- Se requieren al menos tres caras de calidad para formar un grupo automático.
- El clustering es probabilístico: revisa siempre `revision` y los grupos antes
  de entregar material.
- Las rutas extremadamente largas siguen sujetas a la configuración de Windows.
- La herramienta organiza fotos; no identifica nombres ni garantiza anonimato.

## Privacidad

Las imágenes y embeddings se procesan localmente y no se suben por el programa.
Después de instalar dependencias y descargar el modelo, el análisis puede
funcionar offline. El usuario es responsable del consentimiento y de las leyes
aplicables a datos biométricos y fotografías.

## Licencias

El código de este repositorio se distribuye bajo la licencia MIT; consulta
[`LICENSE`](LICENSE).

**La licencia del código no cubre automáticamente los modelos.** El modelo
preentrenado `buffalo_l`, descargado por InsightFace, está limitado por sus
términos a investigación no comercial. Para uso profesional o comercial debes
obtener una licencia apropiada de InsightFace o reemplazarlo por modelos cuyos
términos permitan ese uso. Los pesos no se incluyen en este repositorio. Revisa
la [documentación oficial de licencias de modelos de InsightFace](https://github.com/deepinsight/insightface/blob/master/python-package/docs/model_zoo.md).

Las dependencias conservan sus propias licencias. Antes de distribuir una
aplicación o prestar un servicio comercial, revisa las condiciones vigentes de
InsightFace, ONNX Runtime, OpenCV, NumPy, scikit-learn y rawpy.

## Material que no debe publicarse

`.gitignore` excluye `.venv/`, caches, modelos `.onnx`, `banco_prueba/`,
`lfw_test/`, cualquier `resultado*/`, logs y archivos temporales. No subas fotos
de clientes, datasets descargados, embeddings ni pesos de modelos sin permiso y
licencia explícitos.

Los utilitarios de evaluación viven en `scripts/`; no son necesarios para el
uso normal.

## Contribuciones

Issues y pull requests son bienvenidos. Describe el sistema operativo, versión
de Python, formato de imagen y un ejemplo reproducible que no contenga material
privado. No adjuntes fotografías de personas sin autorización.
